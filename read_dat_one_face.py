def read_dat():
    names_list = []
    names_file = open("names_one.dat", "r", encoding="utf-8")
    line = names_file.readline()
    while line != "":
        names_list.append(line[:-1])
        line = names_file.readline()
    names_file.close()

    encodings_list = []
    encodings_file = open("encodings_one.dat", "r", encoding="utf-8")
    line = encodings_file.readline()
    while line != "":
        str_list = line[:-1].strip('[]').split(', ')
        num_list = []
        for str in str_list:
            num_list.append(float(str))
        encodings_list.append(num_list)
        line = encodings_file.readline()
    encodings_file.close()

    return (names_list, encodings_list)