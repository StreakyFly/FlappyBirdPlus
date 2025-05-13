from src.utils import printc


class FakeSupabaseClient:
    def table(self, name):
        return self

    def insert(self, data):
        printc(f"[FakeSupabase] Would insert: {data}", color="gray")
        return self

    def select(self, *args, **kwargs):
        printc(f"[FakeSupabase] Would select: {args}", color="gray")
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def execute(self):
        printc("[FakeSupabase] Would execute query", color="gray")
        return type('FakeResponse', (), {'data': [{'score': '---', 'timestamp': '---'}]})()
