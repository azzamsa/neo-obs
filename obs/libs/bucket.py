import uuid


def buckets(resource):
    """Return all available buckets object."""
    all_buckets = []
    for bucket in resource.buckets.all():
        all_buckets.append(bucket)
    return all_buckets


def gen_random_name(prefix):
    """Take random UUID and append specified prefix."""
    return f"{prefix}-{str(uuid.uuid4())[:13]}"


def create_bucket(resource, bucket_name, random_name=False):
    """Create a bucket with optional random name as a suffix."""
    if random_name:
        bucket_name = gen_random_name(bucket_name)
    resource.create_bucket(Bucket=bucket_name)


def remove_bucket(resource, bucket_name):
    """Remove a bucket."""
    resource.Bucket(bucket_name).delete()


def get_objects(resource, bucket_name):
    """List objects inside a bucket"""
    objects = []
    bucket = resource.Bucket(bucket_name)
    for obj in bucket.objects.all():
        objects.append(obj)
    return objects


def is_exists(resource, bucket_name, object_name):
    objects = get_objects(resource, bucket_name)
    if object_name in [x.key for x in objects]:
        return True
    else:
        return False


def remove_object(resource, bucket_name, object_name):
    """Remove an object in a bucket."""
    if is_exists(resource, bucket_name, object_name):
        resource.Object(bucket_name, object_name).delete()
    else:
        raise ValueError(f"Object not exists: {object_name}")


def download_object(resource, bucket_name, object_name):
    """Download an object in a bucket."""
    if is_exists(resource, bucket_name, object_name):
        resource.Object(bucket_name, object_name).download_file(f"{object_name}")
    else:
        raise ValueError(f"Object not exists: {object_name}")


def upload_object(resource, bucket_name, object_name):
    """Upload an object into bucket."""
    resource.Object(bucket_name, object_name).upload_file(Filename=object_name)


def copy_object(resource, src_bucket, dest_bucket, object_name):
    """Copy an object into other bucket."""
    copy_source = {"Bucket": src_bucket, "Key": object_name}
    resource.Object(dest_bucket, object_name).copy(copy_source)


def move_object(resource, src_bucket, dest_bucket, object_name):
    """Move an object into other bucket.
    Using copy then remove operation.
    """
    copy_object(resource, src_bucket, dest_bucket, object_name)
    remove_object(resource, src_bucket, object_name)


def disk_usage(resource, bucket_name):
    """Calculate dist usage of objects in bucket."""
    objects = get_objects(resource, bucket_name)
    total_objects = len(objects)
    total_size = 0
    for obj in objects:
        total_size += obj.size
    return total_size, total_objects
