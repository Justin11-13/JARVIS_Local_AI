"""Read-only live App Server handshake; no model turn or repository mutation."""
from services.agents.codex import CodexAdapter


def main():
    adapter = CodexAdapter(lambda message: None)
    try:
        result = adapter.start()
        assert isinstance(result, dict)
        threads = adapter.request('thread/list', {'limit': 1})
        assert 'data' in threads
        print('Live initialize / initialized / thread-list passed. No coding turn started.')
    finally:
        adapter.close()


if __name__ == '__main__':
    main()
