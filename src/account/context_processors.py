def permissions(request):
    context = {}

    instances = [request.selected_org]
    ops = [("c", "create"), ("r", "read"), ("u", "update"), ("d", "delete")]

    for instance in instances:
        if not instance:
            continue
        for namespace in instance.permission_namespaces:
            for op, name in ops:
                key = "{}_{}_{}".format(
                    name, instance.HandleRef.tag, namespace.replace(".", "__")
                )
                context[key] = request.perms.check([instance, namespace], op, ignore_grant_all=True)

    return {"permissions": context}
