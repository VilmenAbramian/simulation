    # Обработка полученных результатов
    from tabulate import tabulate
    # result_processing(kwargs, result, variadic)

    # print(f"[+] Estimating speed = {speed} kmph, Tari = {tari*1e6:.2f} us, "
    #       f"M = {encoding}, tid_size = {tid_word_size} words, "
    #       f"reader_offset = {reader_offset} m, tag_offset = {tag_offset} m, "
    #       f"altitude = {altitude} m, power = {power} dBm, "
    #       f"num_tags = {num_tags}")

    # result['encoding'] = encoding.name
    # result['tari'] = f"{tari * 1e6:.2f}"
    # result['speed'] = speed
    # result['tid_word_size'] = tid_word_size
    # result['reader_offset'] = reader_offset
    # result['tag_offset'] = tag_offset
    # result['altitude'] = altitude
    # result['power'] = power

# Вывод результата для одиночной симуляции
    print(tabulate([(key, value) for key, value in ret.items()],
                    tablefmt='pretty'))
      
      
        # Результаты выводим в двух таблицах: таблице параметров и
        # таблице результатов. В последней - значение изменяющегося аргумента
        # и результаты, которые ему соответсвуют.
        params_names = list(var_arg_names) + ["encoding", "tari", "num_tags"]
        params_names.remove(variadic)

        print("\n# PARAMETERS:\n")
        print(tabulate([(name, kwargs[name]) for name in params_names],
                       tablefmt='pretty'))

        # Подготовим таблицу результатов.
        # Какие ключи нужны из словарей в списке ret (который вернул pool.map):
        # FIXME: ошибка в добавлении столбца с изменяющимся параметром
        # ret_cols = (variadic, "read_tid_prob", "inventory_prob",
        #             "rounds_per_tag")
        ret_cols = ("read_tid_prob", "inventory_prob",
                    "rounds_per_tag")
        print('ret_cols :', ret_cols)
        print('ret: ', ret)
        # Строки таблицы результатов:
        results_table = [[item[column] for column in ret_cols] for item in ret]
        print("\n# RESULTS:\n")
        print(tabulate(results_table, headers=ret_cols, tablefmt='pretty'))