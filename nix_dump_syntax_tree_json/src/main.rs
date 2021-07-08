use std::{env, fs};

fn main() {
    let mut iter = env::args().skip(1).peekable();
    if iter.peek().is_none() {
        eprintln!("Usage: nix_dump_syntax_tree_json <file>");
        return;
    }
    for file in iter {
        let content = match fs::read_to_string(file) {
            Ok(content) => content,
            Err(err) => {
                eprintln!("error reading file: {}", err);
                return;
            }
        };
        let ast = rnix::parse(&content);

        for error in ast.errors() {
            println!("error: {}", error);
        }

        serde_json::to_writer(std::io::stdout(), &ast.node()).unwrap();
    }
}
