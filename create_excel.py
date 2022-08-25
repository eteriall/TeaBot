import json

import xlsxwriter


def export(filename='tea.xlsx'):
    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet()

    green_top_format = workbook.add_format()
    green_top_format.set_pattern(1)  # This is optional when using a solid fill.
    green_top_format.set_bg_color('#A0E09F')
    green_top_format.set_align('center')

    centered = workbook.add_format()
    centered.set_align('center')

    worksheet.set_column(0, 3, 15, cell_format=centered)

    with open('db.json', mode='r') as f:
        data = json.load(f)
        res = {}
        for uid in data:
            p = data[uid]
            room = p['room']
            name = p['name']
            prefs = p['prefs']
            print(prefs)
            for pref in prefs:
                date, time, selection = pref.split(';')
                if date not in res:
                    res[date] = {}
                if time not in res[date]:
                    res[date][time] = {}
                res[date][time][room] = (selection, name)

    worksheet.write(0, 0, "Комната", )
    worksheet.write(0, 1, "Чай", )
    worksheet.write(0, 2, "Никнейм", )
    row = 1
    for date in res:
        for time in res[date]:
            green, black, hot_water = 0, 0, 0
            row += 1
            s_pos = f'A{row}:C{row}'
            for room in sorted(res[date][time]):
                selection = res[date][time][room]
                counter = {'n': lambda b, g, h: (b, g, h),
                           'b': lambda b, g, h: (b + 1, g, h),
                           'g': lambda b, g, h: (b, g + 1, h),
                           'h': lambda b, g, h: (b, g, h + 1),
                           }[selection[0]]
                green, black, hot_water = counter(green, black, hot_water)

                tea = {'n': "-", 'b': 'Чёрный', 'g': 'Зелёный', 'h': 'Кипяток'}[selection[0]]
                worksheet.write(row, 0, room)
                worksheet.write(row, 1, tea)
                worksheet.write(row, 2, selection[1])
                row += 1
            worksheet.merge_range(s_pos, f"{date} Августа, {time} | {green} Зелёных, "
                                         f"{black} Чёрного, {hot_water} Кипяток", green_top_format)

            row += 1
        row += 1

    workbook.close()


if __name__ == "__main__":
    export('tea.xlsx')
