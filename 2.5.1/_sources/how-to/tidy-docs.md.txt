Tidying the dodal docs
======================

The dodal documentation gradually accumulates a quantity of "ghost" files in the
`main` folder of the `gh-pages` branch that are not deleted, due to operation of 
the `gh-pages` github action to support multiple versions of the documentation.

To remedy this, create a separate workspace using `git worktree` and prune the excess pages by doing the following (replace 1.62.0 with whatever the most recent version is):

```
git worktree add ../gh-pages --checkout gh-pages
cd ../gh-pages
diff -rq 1.62.0 main | grep "Only in main" > diff.txt

```

In your favourite editor, find and replace the output in diff.txt with the following regex

`Only in (main[^:] *): (.*)` replace with `$1/$2`

then after saving it

```commandline
for f in `cat diff.txt`; do rm -r $f; done
git add -u main
git status # Check the files over to make sure this is what you expect
git commit --no-verify
git push
```

Once pushed, GitHub CI should automatically run and push the pages to github docs.

In order to avoid potentially removing some files due to differences between main and the 
last release, ideally do this just after a fresh release). Although any files thus missing 
should reappear after then next PR merge.
