Make a new skill called `crosslink-bulk` (triggered by command `/crosslink-bulk` exclusively) which does the following:
1. Look into the folder `/vaults` and check for folder vaults (books), that are not present in `/workspace` folder. 
These books need to be copied to `/workspace` and being crosslinked there. So, for each folder vault (book) that needs to be copied and processed make the following:
    - a) Copy the folder and its content, from `/vaults/[book]` to `/workspace/[book]`.
    - b) For that book, perform the command `/book-crosslink2 [book]` for that book.
     
2. Look for markdown files at the root of `/vaults` whose have prefix as "learning-roadmap" (F.E. "learning-roadmap-type-theory.md", "learning-roadmap-sat-smt-csp.md" and so on). Check for those files that aren't present in `workspace`, and then copy them.
3. At last, execute the command for crossreferencing the "learning-roadmap" notes, as `/book-crosslink2 --curate-learning-roadmaps`.
