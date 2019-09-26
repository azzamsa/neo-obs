import mock
import pytest
from click.testing import CliRunner


from datetime import datetime
from obs.main import cli
import obs.libs.bucket
import obs.libs.auth


def fake_resource():
    pass


@pytest.fixture
def resource(monkeypatch):
    monkeypatch.setattr(obs.libs.auth, "resource", fake_resource)


def fake_buckets(resource):
    bucket1 = mock.Mock()
    bucket1.name = "bucket-one"
    dt1 = datetime(2019, 9, 24, 1, 1, 0, 0)
    bucket1.creation_date = dt1

    bucket2 = mock.Mock()
    bucket2.name = "bucket-two"
    bucket2.creation_date = dt1

    return [bucket1, bucket2]


def test_ls(monkeypatch, resource):
    monkeypatch.setattr(obs.libs.bucket, "buckets", fake_buckets)

    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "ls"])

    assert result.output == (
        f"2019-09-24 01:01:00 bucket-one\n" f"2019-09-24 01:01:00 bucket-two\n"
    )


def fake_get_objects(resource, bucket_name, prefix=""):
    obj1 = mock.Mock()
    obj1.key = "obj-one"
    obj1.size = 100
    dt1 = datetime(2019, 9, 24, 1, 1, 0, 0)
    obj1.last_modified = dt1

    obj2 = mock.Mock()
    obj2.key = "obj-two"
    obj2.size = 200
    obj2.last_modified = dt1

    return [obj1, obj2]


def test_ls_storage(monkeypatch, resource):
    monkeypatch.setattr(obs.libs.bucket, "get_objects", fake_get_objects)

    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "ls", "bucket-one"])

    assert result.output == (
        f"2019-09-24 01:01:00, 100.0 B, obj-one\n"
        f"2019-09-24 01:01:00, 200.0 B, obj-two\n"
    )


def test_disk_usage(monkeypatch, resource):
    monkeypatch.setattr(obs.libs.bucket, "get_objects", fake_get_objects)

    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "du", "bucket-one"])

    assert result.output == (f'300.0 B, 2 objects of "bucket-one" bucket\n')


def fake_bucket_info(resource, bucket_name):
    acl = [[["Test user"], ["FULL_CONTROL"]], [["Public"], ["FULL_CONTROL"]]]
    info = {
        "ACL": acl,
        "CORS": None,
        "Policy": None,
        "Expiration": None,
        "Location": "US",
    }

    return info


def test_bucket_info(monkeypatch, resource):
    monkeypatch.setattr(obs.libs.bucket, "bucket_info", fake_bucket_info)

    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "info", "bucket-one"])

    assert result.output == (
        f"Location: US\n"
        f"Expiration Rule: None\n"
        f"Policy: None\n"
        f"CORS: None\n"
        f"ACL: ['Test user'] : ['FULL_CONTROL']\n"
        f"ACL: ['Public'] : ['FULL_CONTROL']\n"
    )


def fake_object_info(resource, bucket_name, object_name):
    acl = [[["Test user"], ["FULL_CONTROL"]]]
    dt = datetime(2019, 9, 24, 13, 18, 7, 0)
    info = {
        "ACL": acl,
        "Size": 300,
        "LastModified": dt,
        "MD5": "5610180790cf66a71cf5ea9ad0f920f5",
        "MimeType": "binary/octet-stream",
        "StorageClass": None,
    }

    return info


def test_object_info(monkeypatch, resource):
    monkeypatch.setattr(obs.libs.bucket, "object_info", fake_object_info)

    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "info", "bucket-one", "logo.png"])

    assert result.output == (
        f"File Size: 300.0 B\n"
        f"Last Modified: 2019-09-24 13:18:07\n"
        f"Mime Type: binary/octet-stream\n"
        f"Storage: None\n"
        "MD5 Sum: 5610180790cf66a71cf5ea9ad0f920f5\n"
        f"ACL: ['Test user'] : ['FULL_CONTROL']\n"
    )


def fake_presign(resource, bucket_name, object_name, expire):
    return "https://myendpotin.net/oneoneone/logo.png?AWSAccessKeyId=62fake123&Signature=rSNa6fake&Expires=15"


def test_presign(monkeypatch, resource):
    monkeypatch.setattr(obs.libs.bucket, "generate_url", fake_presign)

    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "presign", "bucket-one", "logo.png"])

    assert (
        result.output
        == "https://myendpotin.net/oneoneone/logo.png?AWSAccessKeyId=62fake123&Signature=rSNa6fake&Expires=15\n"
    )