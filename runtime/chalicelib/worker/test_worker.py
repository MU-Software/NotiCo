import json

import chalice.app


def test_handler(record: chalice.app.SQSRecord) -> chalice.app.SQSRecord:
    print(record.to_dict(), json.loads(record.body))
    return record


workers = [test_handler]
