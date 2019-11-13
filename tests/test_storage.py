import mock
import pytest
import sys
import obs.libs.bucket
import obs.libs.auth
import obs.libs.gmt

from obs.storage import commands
from datetime import datetime
from obs.main import cli
from click.testing import CliRunner
from obs.storage import bucket
from pathlib import Path


def fake_resource():
    pass


def fake_plain_auth():
    pass


@pytest.fixture
def resource(monkeypatch):
    monkeypatch.setattr(obs.libs.auth, "resource", fake_resource)


@pytest.fixture
def plain_auth(monkeypatch):
    monkeypatch.setattr(obs.libs.auth, "plain_auth", fake_plain_auth)


def fake_buckets(resource):
    bucket1 = mock.Mock()
    bucket1.name = "bucket-one"
    dt1 = datetime(2019, 9, 24, 1, 1, 0, 0)
    bucket1.creation_date = dt1

    bucket2 = mock.Mock()
    bucket2.name = "bucket-two"
    bucket2.creation_date = dt1

    return [bucket1, bucket2]


def test_resources():
    path = str(Path.home()) + "/.config/neo-obs/obs.env"
    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "ls"])
    assert result.output == (
        f"[Errno 2] No such file or directory: '{path}'\n"
        f"Configuration file not available.\n"
        f"Consider running 'obs --configure' to create one\n"
    )


def test_plain_auth(resource):
    path = str(Path.home()) + "/.config/neo-obs/obs.env"
    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "info"])
    assert result.output == (
        f"[Errno 2] No such file or directory: '{path}'\n"
        f"Configuration file not available.\n"
        f"Consider running 'obs --configure' to create one\n"
    )


def test_ls(monkeypatch, resource):
    monkeypatch.setattr(obs.libs.bucket, "buckets", fake_buckets)

    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "ls"])
    assert result.output == (
        f"2019-09-24 01:01:00 bucket-one\n" f"2019-09-24 01:01:00 bucket-two\n"
    )


def test_except_ls(resource):
    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "ls"])
    assert result.output == (
        f"Bucket listing failed. \n" f"'NoneType' object has no attribute 'buckets'\n"
    )


def fake_get_objects(resource, bucket_name, prefix=""):
    obj1 = mock.Mock()
    obj1.key = "obj-one"
    obj1.size = 100
    dt1 = datetime(2019, 9, 24, 1, 1, 0, 0)
    obj1.last_modified = dt1
    obj1.bucket = "bucket-one"

    obj2 = mock.Mock()
    obj2.key = "obj-two"
    obj2.size = 200
    obj2.last_modified = dt1
    obj2.bucket = "bucket-two"

    return [obj1, obj2]


def test_ls_storage(monkeypatch, resource):
    monkeypatch.setattr(obs.libs.bucket, "get_objects", fake_get_objects)

    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "ls", "bucket-two"])

    assert result.output == (
        f"2019-09-24 01:01:00, 100.0 B, obj-one\n"
        f"2019-09-24 01:01:00, 200.0 B, obj-two\n"
    )


def test_except_ls_storage(resource):
    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "ls", "bucket-one"])

    assert result.output == (f"'NoneType' object has no attribute 'Bucket'\n")


def test_else_ls_storage(monkeypatch, resource):
    monkeypatch.setattr(
        obs.libs.bucket, "get_objects", lambda resource, bucket_name, prefix: []
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "ls", "bucket-one"])

    assert result.output == (f'Bucket "bucket-one" is empty\n')


def test_bucket_usage(monkeypatch, resource):
    monkeypatch.setattr(obs.libs.bucket, "get_objects", fake_get_objects)

    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "du", "bucket-one"])

    assert result.output == (f'300.00 Byte, 2 objects in "bucket-one" bucket\n')


def test_except_bucket_usage(resource):
    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "du", "bucket-one"])

    assert result.output == (
        f"Bucket usage fetching failed. \n"
        f"'NoneType' object has no attribute 'Bucket'\n"
    )


def fake_bucket_info(resource, bucket_name, auth):
    acl = [[["Test user"], ["FULL_CONTROL"]], [["Public"], ["FULL_CONTROL"]]]
    info = {
        "ACL": acl,
        "CORS": None,
        "Policy": None,
        "Expiration": None,
        "Location": "US",
        "GmtPolicy": "2 Replication in Midplaza, 1 in Technovillage",
    }

    return info


def test_bucket_info(monkeypatch, resource, plain_auth):
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
        f"Gmt Policy: 2 Replication in Midplaza, 1 in Technovillage\n"
    )


def test_except_bucket_info(resource, plain_auth):
    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "info", "bucket-one"])
    assert result.output == (
        f"Info fetching failed. \n" f"'NoneType' object has no attribute 'Bucket'\n"
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


def test_object_info(monkeypatch, resource, plain_auth):
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


def test_except_object_info(resource, plain_auth):
    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "info", "bucket-one", "logo.png"])

    assert result.output == (
        f"Info fetching failed. \n" f"'NoneType' object has no attribute 'Object'\n"
    )


def fake_presign(resource, bucket_name, object_name, expire):
    return "https://myendpotin.net/oneoneone/logo.png?AWSAccessKeyId=62fake123&Signature=rSNa6fake&Expires=15"


def test_presign(monkeypatch, resource):
    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "presign", "bucket-one", "logo.png"])

    assert (
        result.output == f"URL generation failed. \n"
        f"'NoneType' object has no attribute 'meta'\n"
    )

    monkeypatch.setattr(obs.libs.bucket, "generate_url", fake_presign)
    result = runner.invoke(cli, ["storage", "presign", "bucket-one", "logo.png"])

    assert (
        result.output
        == "https://myendpotin.net/oneoneone/logo.png?AWSAccessKeyId=62fake123&Signature=rSNa6fake&Expires=15\n"
    )


def create_fake_buck(objsize):
    buck = mock.Mock()
    buck.total_objects = len(objsize)
    buck.total_size = sum(objsize)
    return buck.total_size, buck.total_objects


def fake_disk_usage(resource):
    bucket_name = ["green", "black"]
    disk_usages = []
    buck = []
    buck.append(create_fake_buck([100, 200]))
    buck.append(create_fake_buck([400, 150, 250]))
    for bckt, obj in zip(bucket_name, buck):
        disk_usages.append([bckt, obj])
    return disk_usages


def test_except_disk_usage(monkeypatch, resource):
    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "du"])

    assert result.output == (
        f"Disk usage fetching failed. \n"
        f"'NoneType' object has no attribute 'buckets'\n"
    )


def test_disk_usage(monkeypatch, resource):
    monkeypatch.setattr(obs.libs.bucket, "disk_usage", fake_disk_usage)
    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "du"])

    assert result.output == (
        f'300.00 Byte, 2 objects in "green" bucket\n'
        f'800.00 Byte, 3 objects in "black" bucket\n'
        f"---\n"
        f"1.07 KiB Total\n"
    )


def fake_gmt():
    policies = {
        "Jakarta": {"id": "123", "desc": "", "_": ""},
        "Sydney": {"id": "143", "desc": "foo", "_": ""},
    }
    return policies


def test_gmt(monkeypatch, resource):
    monkeypatch.setattr(obs.libs.gmt, "get_policies", fake_gmt)

    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "gmt", "--policy-id"])

    assert result.output == (
        f"Name: Jakarta\n"
        f"Id: 123\n"
        f"Description: No description\n\n"
        f"Name: Sydney\n"
        f"Id: 143\n"
        f"Description: foo\n\n"
    )


def test_notset_gmt(monkeypatch, resource):
    monkeypatch.setattr(obs.libs.gmt, "get_policies", lambda: "notset")

    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "gmt", "--policy-id"])

    assert result.output == (
        f"Can't find Policy file\n"
        f"See '#using-cloudian-hyperstore-extension' in our documentation for more information\n"
    )


def test_except_gmt(monkeypatch, resource):
    monkeypatch.setattr(obs.libs.gmt, "get_policies", lambda: None)

    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "gmt", "--policy-id"])

    assert result.output == (
        f"Show policies failed. \n" f"'NoneType' object is not iterable\n"
    )


def fake_move():
    bucket = mock.Mock()
    bucket.Bucket.return_value = [
        {"Bucket": "bucket1", "Key": ["obj1"]},
        {"Bucket": "bucket2", "Key": ["obj2", "obj3"]},
    ]
    bucket.Object.return_value.copy.side_effect = bucket.Bucket()[1]["Key"].append(
        "obj1"
    )
    bucket.Object.return_value.delete.side_effect = bucket.Bucket()[0]["Key"].remove(
        "obj1"
    )
    return bucket


def test_mv(monkeypatch):
    monkeypatch.setattr(obs.storage.commands, "get_resources", fake_move)
    monkeypatch.setattr(obs.libs.bucket, "is_exists", lambda res, bucket, object: True)

    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "mv", "bucket-one", "bucket-two", "obj1"])

    assert fake_move().Bucket() == [
        {"Bucket": "bucket1", "Key": []},
        {"Bucket": "bucket2", "Key": ["obj2", "obj3", "obj1"]},
    ]


def test_except_mv(resource):
    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "mv", "bucket-one", "bucket-two", "obj1"])

    assert result.output == (
        f"Object moving failed. \n" f"'NoneType' object has no attribute 'Object'\n"
    )


def fake_copy():
    bucket = mock.Mock()
    bucket.Bucket.return_value = [
        {"Bucket": "bucket1", "Key": ["obj1"]},
        {"Bucket": "bucket2", "Key": ["obj2", "obj3"]},
    ]
    bucket.Object.return_value.copy.side_effect = bucket.Bucket()[1]["Key"].append(
        "obj1"
    )
    return bucket


def test_cp(monkeypatch):
    monkeypatch.setattr(obs.storage.commands, "get_resources", fake_copy)

    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "cp", "bucket-one", "bucket-two", "obj1"])

    assert fake_copy().Bucket() == [
        {"Bucket": "bucket1", "Key": ["obj1"]},
        {"Bucket": "bucket2", "Key": ["obj2", "obj3", "obj1"]},
    ]


def test_except_cp(resource):
    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "cp", "bucket-one", "bucket-two", "obj1"])

    assert result.output == (
        f"Object copying failed. \n" f"'NoneType' object has no attribute 'Object'\n"
    )


def fake_remove():
    bucket = mock.Mock()
    bucket.Bucket.return_value = [
        {"Bucket": "bucket1", "Key": ["obj1"]},
        {"Bucket": "bucket2", "Key": ["obj2", "obj3"]},
    ]
    bucket.Object.return_value.delete.side_effect = bucket.Bucket()[0]["Key"].remove(
        "obj1"
    )
    return bucket


def test_rm(monkeypatch):
    monkeypatch.setattr(obs.storage.commands, "get_resources", fake_remove)
    monkeypatch.setattr(obs.libs.bucket, "is_exists", lambda res, bucket, object: True)

    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "rm", "bucket-one", "obj1"])

    assert fake_remove().Bucket() == [
        {"Bucket": "bucket1", "Key": []},
        {"Bucket": "bucket2", "Key": ["obj2", "obj3"]},
    ]


def test_except_rm(monkeypatch):
    monkeypatch.setattr(obs.storage.commands, "get_resources", fake_remove)
    monkeypatch.setattr(obs.libs.bucket, "is_exists", lambda res, bucket, object: False)

    runner = CliRunner()
    result = runner.invoke(cli, ["storage", "rm", "bucket-one", "obj1"])

    assert result.output == (f"Object removal failed. \n" f"Object not exists: obj1\n")
