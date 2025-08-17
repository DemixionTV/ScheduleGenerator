import dearpygui.dearpygui as pygui
import sqlite3
import datetime
import re
import json
import sys

from generator import run_ga, shedule_settings, set_shedule_settings, print_schedule, generate_valid_individual, check_valid_shedule, decode_schedule, shedule_errors
from generator import Group,Auditory,Subject,SheduleSettings


def decode_string(instr : str):
    instr = str(instr)
    big_let_start = 0x00C0
    small_let_end = 0x00FF
    remap_big_let = 0x0410
    alph_shift = remap_big_let - big_let_start
    if sys.platform == 'win32':
        outstr = []
        for i in range(0, len(instr)):
            char_byte = ord(instr[i])
            if char_byte in range(big_let_start, small_let_end + 1):
                char = chr(ord(instr[i]) + alph_shift)
                outstr.append(char)
            elif char_byte == 0x00A8:
                char = chr(0x0401)
                outstr.append(char)
            elif char_byte == 0x00B8:
                char = chr(0x0451)
                outstr.append(char)
            else:
                outstr.append(instr[i])

        return ''.join(outstr)

def hide_show_dates(sender, app_data, user_data):
    if pygui.get_item_configuration(user_data)['show']:
        pygui.configure_item(user_data, show = False)
        date = pygui.get_value(user_data)
        pygui.configure_item(sender, label = convert_date_to_str(date))
    else:
        pygui.configure_item(user_data, show = True)
        pygui.configure_item(sender, label = "Hide")
        
        
        
def convert_date_to_str(date):
    date["month"] += 1
    if int(date["month_day"]) < 10:
        date["month_day"] = f'0{date["month_day"]}'
    if int(date["month"]) < 10:
        date["month"] = f'0{date["month"]}'
    return f'{date["year"] + 1900}-{date["month"]}-{date["month_day"]}'

def convert_datetime_to_str(date):
    date["month"] += 1
    if int(date["month_day"]) < 10:
        date["month_day"] = f'0{date["month_day"]}'
    if int(date["month"]) < 10:
        date["month"] = f'0{date["month"]}'
    if int(date["hour"]) < 10:
        date["hour"] = f'0{date["hour"]}'
    if int(date["min"]) < 10:
        date["min"] = f'0{date["min"]}'
    if int(date["sec"]) < 10:
        date["sec"] = f'0{date["sec"]}'
    return f'{date["year"] + 1900}-{date["month"]}-{date["month_day"]}T{date["hour"]}:{date["min"]}:{date["sec"]}'

def get_datetime_picker(date_picker, time_picker):
    date_info = pygui.get_value(date_picker)
    time_info = pygui.get_value(time_picker)
    date_info['hour'] = time_info['hour']
    date_info['min'] = time_info['min']
    date_info['sec'] = time_info['sec']
    return convert_datetime_to_str(date_info)


    


def extract_table_name(query):
    match = re.search('from (\S+)',query, flags = re.IGNORECASE)
    return match[0].split('from ')[1]


def exctract_datatypes(connection, table_name):
    cursor = connection.cursor()
    cursor.execute(f'pragma table_info({table_name})')
    type_info = {}
    for cid, name, type, notnull, dflt_value, pk in cursor.fetchall():
        type_info[name] = type
    return type_info

def extract_foreign_info(query):
    inner_joins = re.findall(' inner join (\S+)',query, flags=re.IGNORECASE)
    connections = re.findall(' on (\S+)\.(\S+)\s*=\s*(\S+)\.(\S+)',query,flags = re.IGNORECASE)
    table_name = extract_table_name(query)
    foreign_info = {}
    for ij in inner_joins:
        for s in [s.replace(',','') for s in re.findall(ij+'.(\S+)',query.split(' from ')[0])]:
            foreign_info[s] = ij
    table_foreign_key = {}
    for connect in connections:
        if connect[2] == table_name:
            for i in foreign_info:
                if foreign_info[i] == connect[0]:
                    table_foreign_key[i] = connect[3]
        elif connect[0] == table_name:
            for i in foreign_info:
                if foreign_info[i] == connect[2]:
                    table_foreign_key[i] = connect[1]
    print(foreign_info,table_foreign_key, query)
    return foreign_info, table_foreign_key

#print(extract_foreign_info('select hardware.id, hardware_part.hardware_part_name, hardware.price, shop.shop_name, hardware.buy_date, hardware.warranty_end_date, hardware.breakables, hardware.comment from hardware inner join hardware_part on hardware_part.id=hardware.hardware_part inner join shop on shop.id=hardware.shop_id'))


def get_table_id_value(connection, table, column):
    cursor = connection.cursor()
    print(f'select id,{column} from {table}')
    cursor.execute(f'select id,{column} from {table}')
    result = {}
    for id,c in cursor.fetchall():
        result[c] = id
    return result


def execute_table_editor(sender, app_data, user_data):
    query, description, id, connection, foreign_info,foreign_translate, filter, table_types, editable, to_count, create_string, real_fields_id = user_data
    table_name = extract_table_name(query)
    params = {}
    text_params = {}
    all_create_strings = list(create_string.keys())
    for v in create_string.values():
        all_create_strings += v
    print(all_create_strings)
    for desc in description:
        if f'Add/Edit {desc}' in pygui.get_aliases() and pygui.get_value(f'Add/Edit {desc}') not in ['',None]:
            if desc in foreign_info and desc not in all_create_strings:
                params[desc] = get_table_id_value(connection,foreign_info[desc],desc)[decode_string(pygui.get_value(f'Add/Edit {desc}'))]
                text_params[desc] = decode_string(pygui.get_value(f'Add/Edit {desc}'))
            elif desc in all_create_strings:
                params[desc] = real_fields_id[pygui.get_value(f'Add/Edit {desc}')]
            else:
                if table_types[desc] in ['date']:
#                    params[desc] = json.dumps(pygui.get_value(f'Add/Edit {desc}'))
                    d = pygui.get_value(f'Add/Edit {desc}')
                    params[desc] = datetime.datetime(year=d['year']+1900, month=d['month']+1, day=d['month_day'],minute=0,hour=0,second=0).timestamp()
                    text_params[desc] = datetime.datetime(year=d['year']+1900, month=d['month']+1, day=d['month_day'],minute=0,hour=0,second=0).date()#convert_date_to_str(pygui.get_value(f'Add/Edit {desc}'))
                elif table_types[desc] in ['bool','boolean']:
                    params[desc] = int(pygui.get_value(f'Add/Edit {desc}'))
                    text_params[desc] = int(pygui.get_value(f'Add/Edit {desc}'))
                else:
                    params[desc] = decode_string(pygui.get_value(f'Add/Edit {desc}'))
                    text_params[desc] = decode_string(pygui.get_value(f'Add/Edit {desc}'))
#    print(params)
    cursor = connection.cursor()
    if id == None:
        ins_query = f'insert into {table_name} ('
        val = ''
        param_name_list = []
        value_list = []
        for p in params:
            if p in foreign_translate:
                ins_query += f'{foreign_translate[p]}, '
                param_name_list.append(foreign_translate[p])
            else:
                ins_query += f'{p}, '
                param_name_list.append(p)
            val += '?, '
            value_list.append(params[p])
#        print(f'{ins_query[:-2]}) values ({val[:-2]})',value_list)
        cursor.execute(f'{ins_query[:-2]}) values ({val[:-2]})',value_list)
        connection.commit()
        add_table_row(connection,query,filter,table_types, editable, to_count, create_string)

    else:
        update_query = f'update {table_name} set '
        param_list = []
        for p in params:
            if p not in foreign_translate:
                update_query += f'{p} = ?, '
            else:
                update_query += f'{foreign_translate[p]} = ?, '
            param_list.append(params[p])
#        print(f'{update_query[:-2]} where id = ?',param_list + [id], params)
        cursor.execute(f'{update_query[:-2]} where id = ?',param_list + [id])
        connection.commit()
        update_table_row(connection,query,id, filter,table_types, editable, to_count, create_string)
        



def open_table_editor(sender, app_data, user_data):
    try:
        pygui.configure_item(sender,default_value = False)
    except:
        pass
    info:dict = user_data
    id = info.get('id')
    fields = info.get('fields')
    description = info.get('description')
    filter = info.get('filter') or ['id']
    query = info.get('query')
    table_name = extract_table_name(query)
    connection = info.get('connection')
    editable = info.get('editable')
    to_count = info.get('to_count')
    create_string = info.get('create_string') or {}
    cursor = connection.cursor()
    foreign_info, foreign_translate = extract_foreign_info(query)
    table_types = info.get('table_types')
    pygui.delete_item("Add/Edit",children_only=True)

    if id != None:
        pygui.set_item_label("Add/Edit",f'Edit table {table_name}')
    else:
        pygui.set_item_label("Add/Edit",f'Add table {table_name}')
    used_columns = []
    real_fields = {}
    real_fields_id = {'12345':0}
    clear_description = [f[0] for f in description]
    for cs in create_string:
        if fields != None:
            real_fields[cs] = fields[clear_description.index(cs)]
            for f in create_string[cs]:
                real_fields[cs] += ' ' + fields[clear_description.index(f)]
            real_fields[cs] = real_fields[cs].strip()
            

    for desc_num, desc in enumerate(description):
        if desc[0] not in filter:
            if desc[0] not in foreign_info:
                if table_types[desc[0]].lower() in ['text','str','string']:
                    pygui.add_input_text(label = desc[0], parent = "Add/Edit", tag = f'Add/Edit {desc[0]}')
                elif table_types[desc[0]].lower() in ['float','real']:
                    pygui.add_input_text(label = desc[0], tag = f'Add/Edit {desc[0]}',decimal=True,parent = "Add/Edit")
                elif table_types[desc[0]].lower() in ['integer','int']:
                    pygui.add_input_int(label = desc[0], tag = f'Add/Edit {desc[0]}',parent = "Add/Edit")
                elif table_types[desc[0]].lower() in ['boolean','bool']:
                    pygui.add_checkbox(label = desc[0], parent = "Add/Edit", tag = f'Add/Edit {desc[0]}')
                elif table_types[desc[0]].lower() in ['date']:
                    pygui.add_date_picker(parent = "Add/Edit", tag = f'Add/Edit {desc[0]}', default_value={'month':datetime.datetime.now().date().month-1,'month_day':datetime.datetime.now().date().day,'year':datetime.datetime.now().date().year-1900})
                elif table_types[desc[0]].lower() in ['time']:
                    pygui.add_time_picker(parent = "Add/Edit", tag = f'Add/Edit {desc[0]}',default_value={'hour':datetime.datetime.now().time().hour,'minute':datetime.datetime.now().time().minute, 'sec':0})
            else:
                if desc[0] in create_string:
                    s = desc[0] +","+ ",".join(create_string[desc[0]])
                    cursor.execute(f"select id,{s} from {foreign_info[desc[0]]}")
                    answer = cursor.fetchall()
                    info = []
                    for a in answer:
                        info.append(" ".join(a[1:]))
                        if " ".join(a[1:]) not in real_fields_id:
                            real_fields_id[" ".join(a[1:])] = a[0]
                        else:
                            real_fields_id[f'{a[0]},' + " ".join(a[1:])]
                    used_columns += create_string[desc[0]]
                    pygui.add_combo(label = desc[0], parent = "Add/Edit", tag = f'Add/Edit {desc[0]}', items = info)
                elif desc[0] not in used_columns:
                    print(f'select {desc[0]} from {foreign_info[desc[0]]}')
                    cursor.execute(f'select {desc[0]} from {foreign_info[desc[0]]}')
                    info = [i[0] for i in cursor.fetchall()]
                    pygui.add_combo(label = desc[0], parent = "Add/Edit", tag = f'Add/Edit {desc[0]}', items = info)
                
            if fields != None and desc[0] not in used_columns:
                if desc[0] in table_types and table_types[desc[0]].lower() in ['integer','int']:
                    pygui.configure_item(f'Add/Edit {desc[0]}',default_value = int(fields[desc_num]))
                elif desc[0] in table_types and table_types[desc[0]].lower() in ['boolean','bool']:
                    print(fields[desc_num])
                    pygui.configure_item(f'Add/Edit {desc[0]}',default_value = bool(fields[desc_num]))

                elif desc[0] in table_types and table_types[desc[0]].lower() in ['date']:
                    if type(fields[desc_num]) == str:
                        pygui.configure_item(f'Add/Edit {desc[0]}',default_value = json.loads(fields[desc_num]))
                    elif type(fields[desc_num]) == int:
                        d = datetime.datetime.fromtimestamp(fields[desc_num])
                        val = {'month':d.date().month-1,'month_day':d.date().day,'year':d.year-1900}
                        pygui.configure_item(f'Add/Edit {desc[0]}',default_value = val)
                else:
                    pygui.configure_item(f'Add/Edit {desc[0]}',default_value = real_fields.get(desc[0]) or fields[desc_num] or "")
            print(real_fields,real_fields_id)
    pygui.add_button(label = 'Save' if id != None else 'Add', callback = execute_table_editor, user_data=[query, [d[0] for d in description],id,connection, foreign_info,foreign_translate,filter, table_types, editable,to_count, create_string, real_fields_id], parent = "Add/Edit")
    pygui.show_item("Add/Edit")



def update_table_row(connection,query, id, filter, table_types, editable = True, to_count = [], create_string = {}):
    table_name = extract_table_name(query)
    pygui.delete_item(f'MainTab Database {table_name} Row {id}')
    add_table_row(connection,query, filter, table_types, editable,to_count, create_string)


def add_table_row(connection,query, filter, table_types, editable = True, to_count = [], create_string = {}):
    table_name = extract_table_name(query)
    cursor = connection.cursor()
    cursor.execute(query)
    for row in cursor.fetchall():
        if f'MainTab Database {table_name} Row {row[0]}' not in pygui.get_aliases():
            draw_table_row(connection,query,cursor.description,row, filter, table_types,editable, to_count, create_string)

def delete_table_row(sender, app_data, user_data):
    connection, table_name, column, row_id = user_data
    cursor = connection.cursor()
    cursor.execute(f'delete from {table_name} where {column} = ?',[row_id])
    connection.commit()
    pygui.delete_item(f'MainTab Database {table_name} Row {row_id}')

def recount(sender, app_data, user_data):
    table_name, to_count = user_data
    counts = {}
    for tc in to_count:
        counts[tc] = 0.0
    for tc in to_count:
        for alias in pygui.get_aliases():
            if alias.startswith(f'MainTab Database {table_name} Row ') and alias.endswith(f'{tc}_check to count') and pygui.get_value(alias) and pygui.is_item_shown(pygui.get_item_parent(pygui.get_item_parent(alias))):
                counts[tc] += float(pygui.get_value(alias.replace('_check to count','')))
    for tc in counts:
        pygui.configure_item(f'MainTab Database {table_name} to count_row {tc}',default_value = counts[tc])


def draw_table_row(connection,query,description, row, filter, table_types, editable = True, to_count = [], create_string = {}):
    table_name = extract_table_name(query)
    bf = 0
    if f'MainTab Database {table_name} to count_row' in pygui.get_aliases():
        bf = f'MainTab Database {table_name} to count_row'
    clear_description = [d[0] for d in description]
    used_columns = []
    with pygui.table_row(parent = f'MainTab Database {table_name}',tag = f'MainTab Database {table_name} Row {row[0]}', before = bf):
        for info_num, info in enumerate(row[1:]):
            date_str = None
            if description[info_num+1][0] in table_types and table_types[description[info_num+1][0]] in ['date']:
                if type(info) == str:
                    date_str = convert_date_to_str(json.loads(info))
                elif type(info) == int:
                    date_str = datetime.datetime.fromtimestamp(info).date()
#            if info_num == 0:
            if description[info_num+1][0] in to_count:
                with pygui.group(horizontal=True):
                    pygui.add_text(date_str or info or "", tag = f'MainTab Database {table_name} Row {row[0]} {description[info_num+1][0]}')
                    pygui.add_checkbox(default_value=True,user_data=[table_name, to_count], tag = f'MainTab Database {table_name} Row {row[0]} {description[info_num+1][0]}_check to count', callback = recount)
            elif description[info_num+1][0] in create_string:
                n = date_str or info
                for cs in create_string[description[info_num+1][0]]:
                    n += ' ' + row[clear_description.index(cs)]
                    used_columns.append(cs)
                n = n.strip()
                pygui.add_selectable(label=n,height = 23, callback=open_table_editor,user_data={'id':row[0],'fields': row[1:], 'description':description[1:],'query':query,'connection':connection,'filter':filter,'table_types':table_types, 'editable':editable, 'to_count':to_count,'create_string':create_string}, tag = f'MainTab Database {table_name} Row {row[0]} {description[info_num+1][0]}')
            elif description[info_num+1][0] not in used_columns:
                if description[info_num+1][0] in table_types and table_types[description[info_num+1][0]] in ['bool','boolean']:
                    if info:
                        pygui.add_image("ok_texture", width = 23, height = 23)
                    else:
                        pygui.add_text()
                else:
                    pygui.add_selectable(label=date_str or info,height = 23, callback=open_table_editor,user_data={'id':row[0],'fields': row[1:], 'description':description[1:],'query':query,'connection':connection,'filter':filter,'table_types':table_types, 'editable':editable, 'to_count':to_count,'create_string':create_string}, tag = f'MainTab Database {table_name} Row {row[0]} {description[info_num+1][0]}')
                    pygui.bind_item_handler_registry(f'MainTab Database {table_name} Row {row[0]} {description[info_num+1][0]}',f"Database click handler")
        if editable:
            pygui.add_image_button("trash_texture", user_data=[connection, table_name, description[0][0], row[0]], width = 23, height = 23, callback=delete_table_row)


def filter_table(sender, app_data, user_data):
    table_name,to_count = user_data
    val_to_search = decode_string(pygui.get_value(f'Filter_{table_name}'))
    for alias in pygui.get_aliases():
        if alias.startswith(f'MainTab Database {table_name} Row ') and pygui.get_item_type(alias) == 'mvAppItemType::mvTableRow':
            items = [pygui.get_item_label(c) for c in pygui.get_item_children(alias)[1] if pygui.get_item_type(c) == 'mvAppItemType::mvSelectable']
            to_hide = [val_to_search.lower() in item.lower() for item in items]
            if True not in to_hide:
                pygui.hide_item(alias)
            else:
                pygui.show_item(alias)
    recount(None,None,[table_name,to_count])


def draw_table_by_query(parent, connection:sqlite3.Connection, query, editable = True, filter = ['id'],to_count = [], create_string = {}):
    cursor = connection.cursor()
    cursor.execute(query)
    table_name = extract_table_name(query)
    table_types = exctract_datatypes(connection,table_name)
    pygui.add_input_text(label = 'Filter',user_data=[table_name,to_count], callback=filter_table, on_enter=True, tag = f'Filter_{table_name}')
    sub_strings = []
    for cs in create_string:
        sub_strings += create_string[cs]
   
    with pygui.table(tag = f'MainTab Database {table_name}',parent = parent,header_row=True, resizable=False, policy=pygui.mvTable_SizingStretchProp,borders_outerH=True, borders_innerV=True, borders_innerH=True, borders_outerV=True,row_background = True, hideable = True):
        for desc in cursor.description[1:]:
            if desc[0] not in sub_strings:
                pygui.add_table_column(label = desc[0])
        if editable:
            pygui.add_table_column()
        for r in cursor.fetchall():
            draw_table_row(connection,query, cursor.description,r, filter, table_types,editable, to_count, create_string)
        with pygui.table_row(tag = f'MainTab Database {table_name} to count_row'):
            for desc in cursor.description[1:]:
                pygui.add_text("",tag = f'MainTab Database {table_name} to count_row {desc[0]}')
        if len(to_count) == 0:
            pygui.hide_item(f'MainTab Database {table_name} to count_row')
        else:
            recount(None,None,[table_name,to_count])
    if editable:
        pygui.add_image_button("plus_texture",width = 35, height = 35, callback=open_table_editor, user_data={'description':cursor.description,'query':query,'connection':connection,'filter':filter,'table_types':table_types,'editable':editable, 'to_count':to_count,'create_string':create_string}, parent = parent, tag = f'{table_name} plus_button')

def update_filter(sender, app_data, user_data):
    table_name = pygui.get_item_alias(app_data[1]).split(' Row')[0].split('MainTab Database ')[1]
    lab = pygui.get_item_label(app_data[1])
    pygui.configure_item(f'Filter_{table_name}',default_value=lab)
    filter_table(None,None,pygui.get_item_user_data(f'Filter_{table_name}'))




def save_group_teachers(sender, app_data, user_data):
    connection, teachers, group_id, subjects = user_data
    cursor = connection.cursor()
    reversed_teachers = {v:k for k,v in teachers.items()}
    cursor.execute('delete from group_subject_teacher where group_id = ?', (group_id,))
    for subject in subjects:
        l = pygui.get_value(f"Group Teachers lect{subject}") or None
        p = pygui.get_value(f"Group Teachers practice{subject}") or None
        cursor.execute('insert into group_subject_teacher (group_id, subject_id,teacher_lecture_id,teacher_practice_id) values (?, ?, ?, ?)', (group_id, subject, reversed_teachers[l] if l != None else None, reversed_teachers[p] if p != None else None))
    connection.commit()



def reload_group_teachers(sender, app_data, user_data):
    pygui.delete_item(f"Group Teachers")
    pygui.delete_item(f"Group Teachers direction")
    pygui.delete_item(f"Teacher SAVE")
    connection = user_data
    cursor = connection.cursor()
    cursor.execute('select direction_id from group_name where abbreviation = ?', (pygui.get_value(sender),))
    direction_id = cursor.fetchone()[0]
    cursor.execute(f'select name from direction where id = ?', (direction_id,))
    direction_name = cursor.fetchone()[0]
    pygui.add_text(f'Направление подготовки: {direction_name}', parent = "Teacher child window", tag = "Group Teachers direction")
    cursor.execute('select subject_id from educational_program where direction_id = ?', (direction_id,))
    subjects = [row[0] for row in cursor.fetchall()]
    cursor.execute('select subject.id, subject.title from subject')
    subject_titles = {row[0]:row[1] for row in cursor.fetchall()}
    cursor.execute(f'select teacher.id, teacher.surname, teacher.name, teacher.patronomic from teacher')
    teachers = {row[0]:f'{row[1]} {row[2]} {row[3]}' for row in cursor.fetchall()}
    cursor.execute('select group_name.id from group_name where abbreviation = ?', (pygui.get_value(sender),))
    group_id = cursor.fetchone()[0]
    cursor.execute('select group_subject_teacher.teacher_lecture_id, group_subject_teacher.teacher_practice_id, group_subject_teacher.subject_id from group_subject_teacher where group_id = ?', (group_id,))
    group_teachers = {subject:(lecture, practice) for lecture, practice, subject in cursor.fetchall()}
    with pygui.table(tag = f"Group Teachers", resizable=True, policy=pygui.mvTable_SizingStretchProp,borders_outerH=True, borders_innerV=True, borders_innerH=True, borders_outerV=True,row_background = True, hideable = True, parent = "Teacher child window"):
        pygui.add_table_column(label = "Предмет")
        pygui.add_table_column(label = "Преподаватель лекции")
        pygui.add_table_column(label = "Преподаватель практики")
        for subject in subjects:
            cursor.execute('select teacher_id, can_lecture, can_practice from teacher_subject_ where subject_id = ?', (subject,))
            result = cursor.fetchall()
            lect_teachers = []
            practice_teachers = []
            for row in result:
                if row[1]:
                    lect_teachers.append(row[0])
                if row[2]:
                    practice_teachers.append(row[0])
            with pygui.table_row():
                pygui.add_text(subject_titles[subject], tag = f"Group Teachers Subject{subject}")
                pygui.add_combo(items = [teachers[i] for i in lect_teachers], tag = f"Group Teachers lect{subject}", user_data=[connection, teachers, group_id, subjects], callback=save_group_teachers, default_value=teachers[group_teachers[subject][0]] if subject in group_teachers and group_teachers[subject][0] != None else '')
                pygui.add_combo(items = [teachers[i] for i in practice_teachers], tag = f"Group Teachers practice{subject}", user_data=[connection, teachers, group_id, subjects], callback=save_group_teachers,default_value=teachers[group_teachers[subject][1]] if subject in group_teachers and group_teachers[subject][1] != None else '')
#    pygui.add_button(label = "SAVE", user_data=[connection, teachers, group_id, subjects], callback=save_group_teachers, parent = "Teacher child window", tag = "Teacher SAVE")


def can_be_combined(group_id1, group_id2, connection):
    cursor = connection.cursor()
    cursor.execute('select direction_id from group_name where id = ?', (group_id1,))
    direction_id1 = cursor.fetchone()[0]
    cursor.execute('select direction_id from group_name where id = ?', (group_id2,))
    direction_id2 = cursor.fetchone()[0]
    cursor.execute('select subject_id from educational_program where direction_id = ?', (direction_id1,))
    subjects1 = [row[0] for row in cursor.fetchall()]
    cursor.execute('select subject_id from educational_program where direction_id = ?', (direction_id2,))
    subjects2 = [row[0] for row in cursor.fetchall()]
    for subject in subjects1:
        if subject in subjects2:
            return True
    return False

def check_group_combine(sender, app_data, user_data):
    connection,group_id = user_data
    all_checks = pygui.get_item_children("group_checkbox_container")[1]
    for check in all_checks:
        pygui.show_item(check)
    c = {}
    for check1 in all_checks:
        for check2 in all_checks:
            group_id1 = pygui.get_item_user_data(check1)[1]
            group_id2 = pygui.get_item_user_data(check2)[1]
            if pygui.get_value(check1):
                if check1 != check2 and check2 not in c.keys() and not can_be_combined(group_id1, group_id2,connection):
                    c[check2] = True
    for check in c.keys():
        pygui.hide_item(check)
        pygui.set_value(check, False)


def save_group_combine(sender, app_data, user_data):
    connection,groups = user_data
    cursor = connection.cursor()
    cursor.execute('insert into combined_group(abbreviation) values (?) on conflict do nothing', (decode_string(pygui.get_value(sender)),))
    cursor.execute('select id from combined_group where abbreviation = ?', (decode_string(pygui.get_value(sender)),))
    combined_group_id = cursor.fetchone()[0]
    cursor.execute('delete from combined_group_list where combined_group_id = ?', (combined_group_id, ))
    connection.commit()

    for check in pygui.get_item_children("group_checkbox_container")[1]:
        if pygui.get_value(check):
            group_id = pygui.get_item_user_data(check)[1]
            cursor = connection.cursor()
            cursor.execute('insert into combined_group_list(combined_group_id, group_id) values (?,?)', (combined_group_id, group_id))
    connection.commit()

            
    
def load_group_combine(sender, app_data, user_data):
    connection,combined_group_id = user_data
    cursor = connection.cursor()
    cursor.execute('select group_id from combined_group_list where combined_group_id = ?', (combined_group_id,))
    groups = [row[0] for row in cursor.fetchall()]
    all_checks = pygui.get_item_children("group_checkbox_container")[1]
    for check in all_checks:
        pygui.show_item(check)
        pygui.set_value(check,False)
    for group in groups:
        pygui.set_value(f"group_checkbox_{group}",True)
    pygui.set_value("combined_group_name",pygui.get_item_label(sender))
    check_group_combine(sender, app_data, user_data)
    

    
def add_time_slot(sender, app_data, user_data):
    connection,r = user_data
    cursor = connection.cursor()
    start = pygui.get_value('Add time slot start')
    end = pygui.get_value('Add time slot end')
    cursor.execute('insert into time_slot(start_time, end_time) values (?,?)', (f'{start["hour"]}:{start["min"]}',f'{end["hour"]}:{end["min"]}'))
    connection.commit()
    cursor.execute('select id from time_slot where start_time = ? and end_time = ?', (f'{start["hour"]}:{start["min"]}',f'{end["hour"]}:{end["min"]}'))
    slot_id = cursor.fetchone()[0]
    with pygui.table_row(before = r) as row:
        pygui.add_text(f'{start["hour"]}:{start["min"]}')
        pygui.add_text(f'{end["hour"]}:{end["min"]}')
        pygui.add_image_button("trash_texture", user_data=[connection,row,slot_id], callback = delete_time_slot, width = 20, height = 20)

def delete_time_slot(sender, app_data, user_data):
    connection,r,slot_id = user_data
    cursor = connection.cursor()
    cursor.execute('delete from time_slot where id = ?', (slot_id,))
    connection.commit()
    pygui.delete_item(r)


def generate_schedule(sender, app_data, user_data):
#    start_time = pygui.get_value('Generate schedule start date')
#    end_time = pygui.get_value('Generate schedule end date')
#    s_time = datetime.datetime(year=start_time['year']+1900, month=start_time['month']+1, day=start_time['month_day'],minute=0,hour=0,second=0)
#    e_time = datetime.datetime(year=end_time['year']+1900, month=end_time['month']+1, day=end_time['month_day'],minute=0,hour=0,second=0)
#    num_days = (e_time - s_time).days
    connection, num_days = user_data
    cursor = connection.cursor()
    cursor.execute('select time_slot.start_time from time_slot order by time(time_slot.start_time)')
    slots = {i:s_t[0] for i,s_t in enumerate(cursor.fetchall())}
#    print(slots)
    cursor.execute('select id, name, auditory_size, for_disabled from auditory') #Аудитории
    auditories = {}
    for auditory_id, aud_name,aud_size,for_disabled in cursor.fetchall():
        cursor.execute('select software.software_name from auditory_software inner join software on auditory_software.software_id = software.id where auditory_software.auditory_id = ?', (auditory_id,))
        software = [row[0] for row in cursor.fetchall()]
        auditories[str(aud_name)] = Auditory(aud_name,aud_size,software,bool(for_disabled))
    cursor.execute('select group_name.abbreviation, group_size, has_disabled, start_date, end_date, start_time_id from group_name') #Группы
    groups = {}
    for group_abbreviation, group_size, has_disabled, start_date, end_date, start_time_id in cursor.fetchall():
        groups[group_abbreviation] = Group(group_abbreviation,bool(has_disabled),group_size,datetime.datetime.fromtimestamp(int(start_date)),datetime.datetime.fromtimestamp(int(end_date)),start_time_id)
    
    cursor.execute('select id, surname, name, patronomic from teacher') #Преподаватели
    teachers = {row[0]:f'{row[1]} {row[2]} {row[3]}' for row in cursor.fetchall()}
    shedule_items = []
    cursor.execute('select group_name.id, group_name.abbreviation, direction_id from group_name')
    num = 0
    for group_id, group_abbreviation, direction_id in cursor.fetchall():
        cursor.execute('select subject.id, subject.title, educational_program.lecture_count, educational_program.practice_count from educational_program inner join subject on subject.id = educational_program.subject_id where educational_program.direction_id = ?', (direction_id,))
        for subject_id, subject_name, lecture_count, practice_count in cursor.fetchall():
            cursor.execute('select teacher_lecture_id, teacher_practice_id from group_subject_teacher where group_id = ? and subject_id = ?', (group_id,subject_id))
            res = cursor.fetchone()
            if res != None:
                teacher_lecture,teacher_practice = res
                if teacher_lecture != None and teacher_practice != None:
#                    print(group_abbreviation,subject_name,lecture_count,teachers[teacher_lecture],practice_count,teachers[teacher_practice])
                    for i in range(lecture_count):
                        shedule_items.append((group_abbreviation,teachers[teacher_lecture],subject_name,'Лекция',num))
                        num += 1
                    for i in range(practice_count):
                        shedule_items.append((group_abbreviation,teachers[teacher_practice],subject_name,'Практика',num))
                        num += 1
    shedule_requirements = {}
    cursor.execute('select subject.id, subject.title from subject')
    for subject_id,subject_title in cursor.fetchall():
        cursor.execute('select software.software_name from software_subject inner join subject on subject.id = software_subject.subject_id inner join software on software.id = software_subject.software_id where software_subject.subject_id = ?', (subject_id,))
        software_subjects = [row[0] for row in cursor.fetchall()]
        if len(software_subjects) != 0:
            shedule_requirements[subject_title] = software_subjects



    cursor.execute('select start_date, end_date from group_name')
    result = cursor.fetchall()
    min_start_time = min([datetime.datetime.fromtimestamp(int(i[0])) for i in result])
    max_end_time = max([datetime.datetime.fromtimestamp(int(i[1])) for i in result])
#    print(min_start_time,max_end_time)
    settings = SheduleSettings(num_days+1,slots,auditories, groups, shedule_items, shedule_requirements, start_date=min_start_time,end_date=max_end_time)
#    print(num_days+1,slots,auditories, groups, shedule_items, shedule_requirements, min_start_time,max_end_time)
    print(settings.start_date, settings.end_date)
    set_shedule_settings(settings)
    schedule = decode_schedule(generate_valid_individual(),settings)
    print(settings.start_date, settings.end_date)
#    print_schedule(schedule)
#    print(auditories, settings.auditories)
#    print(check_valid_shedule(s))
    schedule = run_ga()
    pygui.set_item_user_data('Schedule date picker',schedule)
    pygui.set_item_user_data('Main Schedule',[settings,schedule, auditories.copy()])
    print(settings.start_date, settings.end_date)

#    print_schedule(schedule)
#    print(check_valid_shedule(schedule))



def update_schdule_generator(sender, app_data, user_data):
    connection, num_days = pygui.get_item_user_data('Schdeule_generator')
    cursor = connection.cursor()
    cursor.execute('select start_date, end_date from group_name')
    result = cursor.fetchall()
    min_start_time = min([datetime.datetime.fromtimestamp(int(i[0])) for i in result])
    max_end_time = max([datetime.datetime.fromtimestamp(int(i[1])) for i in result])
    old_ud = pygui.get_item_user_data('Schedule date picker')
    old_ud[1] = min_start_time
    old_ud[2] = max_end_time
    pygui.set_item_user_data('Schedule date picker',old_ud)
    pygui.set_item_label('Schdeule_generator',f'Сгенерировать расписание с {min_start_time.date()} по {max_end_time.date()}')
    old_ud = pygui.get_item_user_data('Schdeule_generator')
    old_ud[1] = (max_end_time.date() - min_start_time.date()).days
    pygui.set_item_user_data('Schdeule_generator',old_ud)

def load_schedule(sender, app_data, user_data):
    schedule_settings, shedule, auditories = pygui.get_item_user_data('Main Schedule')
#    shedule = pygui.get_item_user_data('Schedule date picker')
    if schedule_settings == None:
        return
    print(shedule_settings.start_date, shedule_settings.end_date)
    print(shedule_settings.auditories, auditories)
    num_busy = 0
    busy = []
    d = pygui.get_value(sender)
    dat = datetime.date(year=d['year']+1900, month=d['month']+1, day=d['month_day'])
#    if dat < shedule_settings.start_date or dat > shedule_settings.end_date:
#        return
    day = (dat - shedule_settings.start_date).days
    print(f'Day: {day}', schedule_settings.start_date,shedule_settings.end_date, dat, shedule_settings.__dict__)
    for time_slot in range(shedule_settings.num_times):
        for auditory_index in range(len(auditories)):
            auditory_number = list(auditories.keys())[auditory_index]
            start_time = shedule_settings.time_slots[time_slot]
            if shedule[day][time_slot, auditory_index] is not None:
#                    print(f"  Время {time_slot + 1}, Аудитория {shedule_settings.auditories[auditory_number]}: {shedule[day][time_slot, auditory_index]}")
                pygui.bind_item_theme(f'Schedule_matrix_{start_time}_{auditories[auditory_number]}',"Cell is used for Studying")
                num_busy += 1
                busy.append(shedule[day][time_slot, auditory_index])
            else:
                pygui.bind_item_theme(f'Schedule_matrix_{start_time}_{auditories[auditory_number]}',"Cell is free")

#    print(f'Вставлено ячеек: {num_busy}/{len(shedule_settings.shedule_items)}')
#    print(f'Свободные ячейки: {count_schedule_cells() - num_busy} / {count_schedule_cells()}')
#    print('Не получилось вставить в расписание:')
#    for elem in shedule_settings.shedule_items:
#        if elem not in busy:
#            print(elem, "Ошибка: ",shedule_errors[elem] if elem in shedule_errors.keys() else "Ошибка неизвестна")
#    d = pygui.get_value(sender)
#    dat = datetime.datetime(year=d['year']+1900, month=d['month']+1, day=d['month_day'],minute=0,hour=0,second=0)
#    if dat < start_time or dat > end_time:
#        return
#    day_num = (dat - start_time).days
#    print(schedule[day_num])
#    auditories, slots = pygui.get_item_user_data('Main Schedule')
#    for time_slot_index in range(len(slots)):
#        for auditory_index in range(len(auditories)):
#            auditory = auditories[auditory_index]
#            start_time, end_time = slots[time_slot_index]
#            if schedule[day_num][time_slot_index, auditory_index] != None:
#                group, teacher, subject, lesson_type, index = schedule[day_num][time_slot_index, auditory_index]
#                pygui.configure_item(f'Schedule_matrix_{start_time}_{end_time}_{auditory}',fill = [0,255,0])
#                pygui.bind_item_theme(f'Schedule_matrix_{start_time}_{end_time}_{auditory}',"Cell is used for Studying")
#                pygui.configure_item(f'Schedule_matrix_{start_time}_{end_time}_{auditory}_image',show = True)
#                pygui.configure_item(f'Schedule_matrix_{start_time}_{end_time}_{auditory}_text', default_value = f'{group}:{teacher}\n{subject}|{lesson_type}\n{auditory}')
#            else:
#                pygui.bind_item_theme(f'Schedule_matrix_{start_time}_{end_time}_{auditory}',"Cell is free")
#                pygui.configure_item(f'Schedule_matrix_{start_time}_{end_time}_{auditory}',fill = [0,0,0])
#                pygui.configure_item(f'Schedule_matrix_{start_time}_{end_time}_{auditory}_image',show = False)


def get_last_item_id(connection,table_name):
    cursor = connection.cursor()
    cursor.execute(f"select max(id) from {table_name}")
    return cursor.fetchall()[0][0]


def delete_direction(sender, app_data, user_data):
    connection, row, slot = user_data
    cursor = connection.cursor()
    cursor.execute(f'delete from direction where id = ?', (row,))
    pygui.delete_item(row)

def save_direction_editor(sender, app_data, user_data):
    connection = user_data
    cursor = connection.cursor()
    direct = decode_string(pygui.get_value("Add/Edit_Name"))
    count = pygui.get_value("Add/Edit_Courses")
    for i in range(count):
        cursor.execute('insert into direction(name) values(?)', (f'{direct} {i+1} курс',))
        connection.commit()
        last_id = get_last_item_id(connection,"direction")
        with pygui.table_row(parent = f'MainTab Database direction') as r:
#            pygui.add_text(last_id)
            pygui.add_text(f'{direct} {i+1} курс')
            pygui.add_image_button('trash_texture', user_data=[connection, r, last_id], callback=delete_direction, width = 20, height = 20)




def load_direction_editor(sender, app_data, user_data):
    connection = user_data
    pygui.delete_item("Add/Edit",children_only=True)
    pygui.set_item_label("Add/Edit",f'Add table direction')
    pygui.add_input_text(label = "Название направления",tag="Add/Edit_Name",width=200, parent = "Add/Edit")
    pygui.add_input_int(label = "Количество курсов",tag="Add/Edit_Courses",width=200, min_clamped=True, min_value=1, default_value=4, parent = "Add/Edit")
    pygui.add_button(label= "Add", user_data=connection, callback=save_direction_editor, parent = "Add/Edit")
    pygui.show_item("Add/Edit")

def reload_database():
    pygui.delete_item(f"Database click handler")
    with pygui.item_handler_registry(tag = f"Database click handler"):
        pygui.add_item_clicked_handler(button = pygui.mvMouseButton_Right, callback=update_filter)
    connection = sqlite3.connect('Schedule.db', check_same_thread=False)
    cursor = connection.cursor()
    cursor.execute('create table if not exists time_slot(id integer primary key autoincrement, start_time text unique, end_time text unique)') #Время проведения занятий
    cursor.execute('create table if not exists teacher (id integer primary key autoincrement, surname text, name text not null, patronomic text)') #Преподаватели
    cursor.execute('create table if not exists direction (id integer primary key autoincrement, name text not null)') #Направления подготовки
    cursor.execute('create table if not exists subject (id integer primary key autoincrement, title text not null)') #Предметы
    cursor.execute('create table if not exists teacher_subject_ (id integer primary key autoincrement, teacher_id integer not null, subject_id integer not null, can_lecture bool, can_practice bool, foreign key (teacher_id) references teacher(id), foreign key (subject_id) references subject(id))') #Предметы преподавателей
    cursor.execute('create table if not exists group_name (id integer primary key autoincrement, abbreviation text not null, direction_id integer not null, group_size integer, start_date date, end_date date has_disabled bool, start_time_id integer, foreign key (direction_id) references direction(id), foreign key (start_time_id) references time_slot(id))') #Группы
    cursor.execute('create table if not exists combined_group(id integer primary key autoincrement, abbreviation text unique)')
    cursor.execute('create table if not exists combined_group_list(id integer primary key autoincrement, combined_group_id integer not null, group_id integer not null, foreign key (combined_group_id) references combined_group(id), foreign key (group_id) references group_name(id))')
    cursor.execute('create table if not exists auditory (id integer primary key autoincrement, name text not null, auditory_size integer, for_disabled bool)') #Аудитории
    cursor.execute('create table if not exists software(id integer primary key autoincrement, software_name text not null)') #Программы
    cursor.execute('create table if not exists software_subject (id integer primary key autoincrement, subject_id integer not null, software_id integer not null, foreign key (subject_id) references subject(id), foreign key (software_id) references software(id))') #ПО для предметов
    cursor.execute('create table if not exists auditory_software (id integer primary key autoincrement, auditory_id integer not null, software_id integer not null, foreign key (auditory_id) references auditory(id), foreign key (software_id) references software(id))') #ПО в аудиториях
    cursor.execute('create table if not exists educational_program (id integer primary key autoincrement, direction_id integer, subject_id integer, lecture_count int, practice_count int, foreign key (direction_id) references direction(id), foreign key (subject_id) references subject(id))') #Образовательные программы
    cursor.execute('create table if not exists group_subject_teacher (id integer primary key autoincrement, group_id int, subject_id integer, teacher_lecture_id, teacher_practice_id, foreign key (group_id) references group_name(id), foreign key (subject_id) references subject(id), foreign key (teacher_lecture_id) references teacher(id), foreign key (teacher_practice_id) references teacher(id))') #Предметы групп


#    cursor.execute('create table if not exists program ')
#    cursor.execute('create table if not exists shop (id integer primary key autoincrement, shop_name text not null)')
#    cursor.execute('create table if not exists hardware_category (id integer primary key autoincrement, hardware_category_name text not null)')
#    cursor.execute('create table if not exists hardware_type (id integer primary key autoincrement, hardware_type_name text not null, hardware_category integer not null, foreign key (hardware_category) references hardware_category(id))')
#    cursor.execute('create table if not exists hardware_part (id integer primary key autoincrement, hardware_part_name text not null, hardware_type int not null, foreign key (hardware_type) references hardware_type(id))')
#    cursor.execute('create table if not exists hardware (id integer primary key autoincrement, hardware_part integer not null, price real not null, shop integer not null, buy_date date, warranty_end_date date, breakables text, comment text, foreign key (hardware_part) references hardware_part(id), foreign key (shop) references shop(id))')
    connection.commit()
    with pygui.tab_bar(parent = "Shedule", callback=update_schdule_generator):
        with pygui.tab(label = "Преподаватели") as p:
            query = 'select teacher.id, teacher.surname, teacher.name, teacher.patronomic from teacher'
            draw_table_by_query(p,connection,query)
        with pygui.tab(label = "Направления подготовки") as p:
            query = 'select direction.id, direction.name from direction'
            draw_table_by_query(p,connection,query)
            pygui.delete_item(f'direction plus_button')
            pygui.add_image_button("plus_texture",width = 35, height = 35, callback=load_direction_editor, tag = f'direction plus_button', user_data=connection)
        with pygui.tab(label = "Предметы") as p:
            query = 'select subject.id, subject.title from subject'
            draw_table_by_query(p,connection,query)
        with pygui.tab(label = "Предметы преподавателей") as p:
            query = "select teacher_subject_.id, teacher.surname, teacher.name, teacher.patronomic, subject.title, teacher_subject_.can_lecture, teacher_subject_.can_practice from teacher_subject_ inner join teacher on teacher.id = teacher_subject_.teacher_id inner join subject on subject.id = teacher_subject_.subject_id"
            draw_table_by_query(p,connection,query,create_string={'surname':['name','patronomic']})
        with pygui.tab(label = "Образовательные программы") as p:
            query = "select educational_program.id, direction.name, subject.title, educational_program.lecture_count, educational_program.practice_count from educational_program inner join subject on subject.id = educational_program.subject_id inner join direction on direction.id = educational_program.direction_id"
            draw_table_by_query(p,connection,query)
        with pygui.tab(label = "Группы") as p:
            query = 'select group_name.id, group_name.abbreviation, direction.name, group_name.group_size, group_name.has_disabled, group_name.start_date, group_name.end_date, time_slot.start_time from group_name inner join direction on direction.id = group_name.direction_id inner join time_slot on time_slot.id = group_name.start_time_id'
            draw_table_by_query(p,connection,query)
        with pygui.tab(label = 'Объединение групп') as p:
            cursor.execute('select group_name.id, group_name.abbreviation from group_name')
            groups = {row[0]:row[1] for row in cursor.fetchall()}
            cursor.execute('select id, abbreviation from combined_group')
            combined_groups = {row[0]:row[1] for row in cursor.fetchall()}
            with pygui.group(horizontal=True):
                with pygui.child_window(width= 400, height = 800, tag = "group_checkbox_container"):
                    for group_id in groups:
                        pygui.add_checkbox(label = f"{groups[group_id]}", tag=f"group_checkbox_{group_id}", user_data=[connection,group_id], callback = check_group_combine)
                pygui.add_input_text(label="Название объединения", user_data=[connection,groups], width = 400, callback = save_group_combine, on_enter=True, tag = "combined_group_name")
                with pygui.child_window(width= 400, height = 800, tag = "group_combine_list"):
                    for combined_group_id in combined_groups:
                        pygui.add_button(label = combined_groups[combined_group_id], user_data=[connection,combined_group_id], callback = load_group_combine, width = 350, height = 25)
#                pygui.add_button(label = "SAVE", user_data=[connection,groups], callback=save_group_union)
        

        with pygui.tab(label = "Аудитории") as p:
            query = 'select auditory.id, auditory.name, auditory.auditory_size, auditory.for_disabled from auditory'
            draw_table_by_query(p,connection,query)
        with pygui.tab(label = "ПО") as p:
            query = 'select software.id, software.software_name from software'
            draw_table_by_query(p,connection,query)
        with pygui.tab(label = "ПО для предметов") as p:
            query = "select software_subject.id, software.software_name, subject.title from software_subject inner join subject on subject.id = software_subject.subject_id inner join software on software.id = software_subject.software_id"
            draw_table_by_query(p,connection,query)
        with pygui.tab(label = "ПО в аудиториях") as p:
            query = "select auditory_software.id, auditory.name, software.software_name from auditory_software inner join auditory on auditory.id = auditory_software.auditory_id inner join software on software.id = auditory_software.software_id"
            draw_table_by_query(p,connection,query)
        with pygui.tab(label = "Преподаватели в группах") as p:
            cursor = connection.cursor()
            cursor.execute('select group_name.id, group_name.abbreviation from group_name')
            groups = {}
            for group_id, group_name in cursor.fetchall():
                groups[group_name] = group_id
            with pygui.group(horizontal=True):
                pygui.add_listbox(items = list(groups.keys()),num_items=25, width = 200, user_data=connection, callback=reload_group_teachers)
                with pygui.child_window(tag = "Teacher child window"):
                    pass
        with pygui.tab(label = "Время проведения занятий") as p:
            cursor.execute('select time_slot.id, time_slot.start_time, time_slot.end_time from time_slot order by time(time_slot.start_time)')
            with pygui.table(tag = f'Time slots table',header_row=True, resizable=False, policy=pygui.mvTable_SizingStretchProp,borders_outerH=True, borders_innerV=True, borders_innerH=True, borders_outerV=True,row_background = True, hideable = True):
                pygui.add_table_column(label = 'Время начала')
                pygui.add_table_column(label = 'Время конца')
                pygui.add_table_column()
                for slot_id, s_time, e_time in cursor.fetchall():
                    with pygui.table_row() as r:
                        pygui.add_text(s_time)
                        pygui.add_text(e_time)
                        pygui.add_image_button("trash_texture", user_data=[connection,r,slot_id], width=20, height = 20, callback=delete_time_slot)
                
                with pygui.table_row() as r:
                    pygui.add_time_picker(hour24=True, tag = 'Add time slot start')
                    pygui.add_time_picker(hour24=True, tag = 'Add time slot end')
                    pygui.add_image_button("plus_texture",callback = add_time_slot, user_data=[connection,r], width=20, height = 20)
        
#        with pygui.tab(label = "Генерация расписания") as p:
#            with pygui.group(horizontal=True):
#                pygui.add_text('Начало генерации')
#                pygui.add_date_picker(default_value={'month':datetime.datetime.now().date().month-1,'month_day':datetime.datetime.now().date().day,'year':datetime.datetime.now().date().year-1900},tag = 'Generate schedule start date')
#                pygui.add_text('Конец генерации')
#                pygui.add_date_picker(default_value={'month':datetime.datetime.now().date().month-1,'month_day':datetime.datetime.now().date().day,'year':datetime.datetime.now().date().year-1900},tag = 'Generate schedule end date')

            
                
        with pygui.tab(label = "Расписание предметов") as p:
            pygui.add_date_picker(default_value={'month':datetime.datetime.now().date().month-1,'month_day':datetime.datetime.now().date().day,'year':datetime.datetime.now().date().year-1900}, tag = 'Schedule date picker', user_data=[None, None, None], callback=load_schedule)
            pygui.add_button(label='Сгенерировать расписание', callback=generate_schedule, user_data=[connection,0], tag= 'Schdeule_generator')
            auditories = []
            cursor.execute('select name from auditory order by name') #Аудитории
            for aud_name, in cursor.fetchall():
                auditories.append(aud_name)
            cursor.execute('select time_slot.start_time, time_slot.end_time from time_slot')
            slots = [(row[0],row[1]) for row in cursor.fetchall()]
            with pygui.group(tag = 'Main Schedule', user_data=None):
                with pygui.group(horizontal=True):
#                    pygui.add_text(wrap = 200)
                    with pygui.drawlist(width = 50, height = 50):
                        pass
                    for aud in auditories:
                        with pygui.drawlist(width = 50, height = 50):
                            pygui.draw_text((0,0),aud, size = 35)
                    pygui.add_separator()
                for s_time, e_time in slots:
                    with pygui.group(horizontal=True):
                        with pygui.drawlist(width = 50, height = 50):
                            pygui.draw_text((0,0),f'{s_time}\n{e_time}', size = 25)
                        for aud in auditories:
                            with pygui.child_window(tag = f'Schedule_matrix_{s_time}_{aud}', width=50,height = 50, no_scrollbar=True, no_scroll_with_mouse=True) as p:
                                with pygui.tooltip(p):
                                    pygui.add_text(tag = f'Schedule_matrix_{s_time}_{aud}_text')
#                                pygui.add_image(texture_tag="teacher_photo_" + "Grebenyuk",tag = f'Schedule_matrix_{s_time}_{e_time}_{aud}_image', pos = (0,0), width=50, height = 50, show = False)

#                            with pygui.drawlist(width = 50, height = 50):
#                                pygui.draw_rectangle((0,0),(50,50), color = [255,255,255], fill = [0,0,0], tag = f'Schedule_matrix_{s_time}_{e_time}_{aud}')
#                                pygui.draw_image(texture_tag="teacher_photo_" + "Grebenyuk",tag = f'Schedule_matrix_{s_time}_{e_time}_{aud}_image',show=False, pmin = (0,0), pmax = (50,50))


                    pygui.add_separator()
#            pygui.show_style_editor()


            
        
#        with pygui.tab(label = "Программы") as p:
