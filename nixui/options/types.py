import parsimonious


def parse_type(type_str):
    print(type_str)
    tree = NIX_TYPE_GRAMMAR.parse(type_str)
    root_node = NixVisitor().visit(tree)
    assert len(root_node) == 1
    return root_node[0]


NIX_TYPE_GRAMMAR = parsimonious.grammar.Grammar("""
    type =             collection_of / no_criteria_primative / criteria_primative

    collection_of =    or_group / attribute_set_of / list_of

    or_group =         primative " or " type
    attribute_set_of = "attribute set of " type "s"
    list_of =          "list of " type "s"

    primative = criteria_primate / no_criteria_primative
    criteria_primative = primative ", "
    no_criteria_primative = one_of / "null" / "anything" / "unspecified" / "string without spaces"
    primative = "string" / "path" / "package" / "floating point number" / "signed integer" / "integer"

    one_of =           "one of " (quoted comma ws)* (quoted ws)

    comma = ","
    quoted =     ~r'"[^\"]+"'
    ws =         ~r"\s*"
""")


class NixVisitor(parsimonious.nodes.NodeVisitor):
    def visit_type(self, node, visited_children):
        """ Returns the overall output. """
        return visited_children

    def visit_collectionof(self, node, visited_children):
        """ Returns the overall output. """
        token_or_node, = visited_children
        return token_or_node

    def visit_attribute_set_of(self, node, visited_children):
        """ Returns the overall output. """
        name, _, position, _, _, _, elems, _, _ = visited_children
        return Node(name, position, elems)

    def visit_list_of(self, node, visited_children):
        """ Returns the overall output. """
        name, _, quoted, _, _, position, _ = visited_children
        quoted = quoted[1:-1]  # strip quote symbols (TODO: move this to the grammar)
        quoted = quoted.replace('ESCAPEQUOTE', '\"')  # TODO: fix hack (see note 3929 above)
        quoted = quoted.encode('utf-8').decode('unicode_escape')  # unescape
        return Token(name, position, quoted)

    def visit_or_group(self, node, visited_children):
        return node.text.split('..')

    def visit_criteria_primative(self, node, visited_children):
        return node.text.split('..')

    def visit_primative(self, node, visited_children):
        return node.text.split('..')

    def generic_visit(self, node, visited_children):
        return node.text
