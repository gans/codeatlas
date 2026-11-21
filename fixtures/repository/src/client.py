from security import check_acl

@requires_acl("read")
def load_resource():
    return check_acl("read")
