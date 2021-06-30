# from https://stackoverflow.com/questions/800030/remove-carriage-return-in-unix
grep -r --color=never --include="*.sh" $'\r' <filename> # looks for \r in file
sed -i 's/\r$//g' <filename> # fixes the file 