def dict_get_object(dict, kind):
    for o in dict:
        if o == kind:
            return dict[o]
