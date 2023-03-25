# FictionScript
#####_A language for the word-rotators_

## Anatomy of a FictionScript

This is where I would put an explanation of the syntax if I wasn't feeling lazy at the moment.

## Auto-Loading .fic files

### fictionsuit/fic/

Any `.fic` file inside the `ficitonsuit/fic` folder will be automatically loaded as a fictionscript when the application starts.

The script will be loaded into a variable with a name determined by the script's filename. The `.fic` extension will be removed, underscores will be replaced with spaces, and all characters will be converted to lower case.

For example:
`fictionsuit/fic/DnD_character.fic` will be loaded into the variable `dnd character`, and the script would be executed with `fic dnd character: {args}`

#### Changes

When making changes to the fictionscript syntax, we should always make sure to update the files in `fic/` to use the new syntax.

### fictionsuit/.fic/

Scripts in the `.fic/` folder will be loaded just like the ones in the `fic/` folder. The only difference is that the `.fic/` folder is gitignored. This is for private scripts, or in-development scripts that are not ready to be added to the repo.

If a script from `.fic/` has the same name as a script from `fic/`, it will overwrite it, due to the order in which the folders are loaded. So, you can override or modify the functionality of a ficscript locally by simply copying it out of the `fic/` folder before you make your changes.
