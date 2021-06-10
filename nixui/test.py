AST_DUMP_GRAMMAR.parse("""
NODE_PAT_ENTRY 125..141 {
  NODE_IDENT 125..129 {
    TOKEN_IDENT("cpio") 125..129
  }
}
""".strip())

# above works


AST_DUMP_GRAMMAR.parse("""
NODE_PAT_ENTRY 125..141 {
  NODE_IDENT 125..129 {
    TOKEN_IDENT("cpio") 125..129
  }
  TOKEN_WHITESPACE(" ") 129..130
  TOKEN_QUESTION("?") 130..131
}
""".strip())

# above produces the following error:
"""
Traceback (most recent call last):
  File "api.py", line 5, in <module>
    import containers, parser
  File "/home/andrew/p/nix-gui/src/parser.py", line 81, in <module>
    AST_DUMP_GRAMMAR.parse(""
  File "/nix/store/agjny99n2ny4pc5zn46pima7rabb2ysq-python3.8-parsimonious-0.8.1/lib/python3.8/site-packages/parsimonious/grammar.py", line 115, in parse
    return self.default_rule.parse(text, pos=pos)
  File "/nix/store/agjny99n2ny4pc5zn46pima7rabb2ysq-python3.8-parsimonious-0.8.1/lib/python3.8/site-packages/parsimonious/expressions.py", line 120, in parse
    node = self.match(text, pos=pos)
  File "/nix/store/agjny99n2ny4pc5zn46pima7rabb2ysq-python3.8-parsimonious-0.8.1/lib/python3.8/site-packages/parsimonious/expressions.py", line 137, in match
    raise error
parsimonious.exceptions.ParseError: Rule 'rbracket' didn't match at '' (line 7, column 2).
"""
