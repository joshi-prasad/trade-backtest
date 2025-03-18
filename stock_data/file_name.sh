# for file in *; do
#     # get file extension
#     ext="${file##*.}"
#     # get file name
#     name="${file%.*}"
#     # check if file extension contains csv then skip the file, else move the file with csv extension
#     if [ "$ext" == "csv" ]; then
#         echo "File already has csv extension"
#     else
#         mv "$file" "$name.csv"
#     fi
#     file="$name.csv"

#     # if the first line of the file contains the file's name, then delete the first line of the file
#     if head -n 1 "$file" | grep -q "$name"; then
#         tail -n +2 "$file" > "$file.tmp" && mv "$file.tmp" "$file"
#     fi
# done

for file in nse_100_data*.csv; do
    # echo "${file}"
    first_line=$(head -n 1 "${file}")
    # remove any comma at the end of the line
    first_line=$(echo "${first_line}" | cut -f1 -d',')
    if [[ "${first_line}" =~ ^Date ]]; then
        echo "File ${file} starts with Date"
        continue
    fi
    file_name="${first_line}.csv"
    tail -n +2 "$file" > "$file.tmp" && mv "$file.tmp" "$file_name"
    rm "$file"
    echo "File ${file} has been renamed to ${file_name}"
done