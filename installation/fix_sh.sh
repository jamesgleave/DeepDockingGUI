grep -r --color=never --include="*.sh" $'\r' <filename> # looks for \r in file
sed -i 's/\r$//g' <filename> # fixes the file 