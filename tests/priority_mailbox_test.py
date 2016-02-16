import unittest

# from queue import PriorityQueue
import time

#from pykka.proxy import priority
from pykka.proxy import priority
from pykka.threading import PriorityQueueMailbox, ThreadingActorPriorityMailbox


class PriorityMailBoxTest(unittest.TestCase):
    def setUp(self):
        self.queue = PriorityQueueMailbox()

    def test_put_without_prio(self):
        # item with default prio
        item_1 = {'the_test1': 'with a dict', 'and': 'other values'}
        self.queue.put(item_1)

        item_2 = {'the_test2': 'with a dict', 'and': 'other values'}
        self.queue.put(item_2)

        item_3 = {'the_test3': 'with a dict', 'and': 'other values'}
        self.queue.put(item_3)

        # item with lower value = higher prio
        item_4 = {'the_test4': 'with a dict'}
        self.queue.put(item_4)

        self.assertEqual(item_1, self.queue.get())
        self.assertEqual(item_2, self.queue.get())
        self.assertEqual(item_3, self.queue.get())
        self.assertEqual(item_4, self.queue.get())

    def test_with_priority(self):
        # item with default prio
        item_1 = {'the_test1': 'with a dict', 'and': 'other values', 'pykka_priority': 30}
        self.queue.put(item_1)

        item_2 = {'the_test2': 'with a dict', 'and': 'other values', 'pykka_priority': 10}
        self.queue.put(item_2)

        item_3 = {'the_test3': 'with a dict', 'and': 'other values', 'pykka_priority': 20}
        self.queue.put(item_3)

        self.assertEqual(item_2, self.queue.get())
        self.assertEqual(item_3, self.queue.get())
        self.assertEqual(item_1, self.queue.get())


class AnActor(ThreadingActorPriorityMailbox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.call_order = []

    def on_receive(self, message):
        if message.get('call_order'):
            return self.call_order
        time.sleep(1)
        self.call_order.append(message['num'])
        return message['num']


class AnProxyActor(ThreadingActorPriorityMailbox):
    def __init__(self):
        ThreadingActorPriorityMailbox.__init__(self)
        self.call_order = []

    @priority(40)
    def important(self):
        time.sleep(0.4)
        self.call_order.append('important')

    @priority(30)
    def more_important(self):
        time.sleep(0.4)
        self.call_order.append('more_important')

    @priority(10)
    def most_important(self):
        time.sleep(0.4)
        self.call_order.append('most_important')


class PrioMbTest(unittest.TestCase):
    def setUp(self):
        self.my_actor_ref = AnActor.start()

    def test_prio_call(self):
        self.my_actor_ref.ask({'pykka_priority': 10, 'num': 1}, block=False)
        self.my_actor_ref.ask({'pykka_priority': 20, 'num': 2}, block=False)
        self.my_actor_ref.ask({'pykka_priority': 10, 'num': 3}, block=False)

        self.assertEqual(self.my_actor_ref.ask({'call_order': True}), [1, 3, 2])

    def tearDown(self):
        self.my_actor_ref.stop()


class PrioMbDecoratorTest(unittest.TestCase):
    def setUp(self):
        self.my_actor_ref = AnProxyActor.start()
        self.proxy = self.my_actor_ref.proxy()

    def test_prio_call(self):
        self.proxy.important()
        time.sleep(0.1)
        self.proxy.more_important()
        time.sleep(0.1)
        self.proxy.most_important()
        time.sleep(0.1)
        self.proxy.important()

        self.assertEqual(self.proxy.call_order.get(),
                         ['important', 'most_important', 'more_important', 'important'])

    def tearDown(self):
        self.proxy.stop()
