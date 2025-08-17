import dearpygui.dearpygui as pygui
import dearpygui.demo as demo
from generator import run_ga
import datetime
from gui import reload_database
import os
pygui.create_context()

#def keyboard_click(event):
#    print(event.name)

#keyboard.on_release(callback=keyboard_click)

with pygui.font_registry():
    big_let_start = 0x00C0
    big_let_end = 0x00DF
    small_let_end = 0x00FF
    remap_big_let = 0x0410
    alph_len = big_let_end - big_let_start + 1
    alph_shift = remap_big_let - big_let_start
    with pygui.font(f'font.otf', 16) as default_font:
        pygui.add_font_range_hint(pygui.mvFontRangeHint_Default)
        pygui.add_font_range_hint(pygui.mvFontRangeHint_Cyrillic)
        biglet = remap_big_let
        for i1 in range(big_let_start, big_let_end + 1):
            pygui.add_char_remap(i1, biglet)
            pygui.add_char_remap(i1 + alph_len, biglet + alph_len)
            biglet += 1
        pygui.bind_font(default_font)

with pygui.theme(tag = "Cell is used for Studying"):
    with pygui.theme_component(pygui.mvAll):
        pygui.add_theme_color(pygui.mvThemeCol_ChildBg, (255, 0, 0), category=pygui.mvThemeCat_Core)

with pygui.theme(tag = "Cell is free"):
    with pygui.theme_component(pygui.mvAll):
        pygui.add_theme_color(pygui.mvThemeCol_ChildBg, (0, 0, 0), category=pygui.mvThemeCat_Core)

with pygui.theme(tag = "Cell is used for Leisure"):
    with pygui.theme_component(pygui.mvAll):
        pygui.add_theme_color(pygui.mvThemeCol_ChildBg, (0, 255, 0), category=pygui.mvThemeCat_Core)


with pygui.texture_registry(show=False, tag = "texture_registry"):       
    w,h,c,d = pygui.load_image("ok.png")
    pygui.add_dynamic_texture(w, h,d, tag = "ok_texture")
    w,h,c,d = pygui.load_image("trash.png")
    pygui.add_dynamic_texture(w, h,d, tag = "trash_texture")
    w,h,c,d = pygui.load_image("plus.png")
    pygui.add_dynamic_texture(w, h,d, tag = "plus_texture")


#with pygui.handler_registry():
#    pygui.add_mouse_move_handler(callback=mouse_move)
#    pygui.add_mouse_down_handler(callback= mouse_down)    
#    pygui.add_mouse_release_handler(callback= mouse_release) 
#    pygui.add_mouse_click_handler(callback=on_click) 
#    pygui.add_mouse_double_click_handler(callback=on_double_click) 
example_schedule_items = [
    (1, "Иванов", "Математика", "Лекция",0),
    (2, "Петров", "Физика", "Лабораторная",1),
    (1, "Сидоров", "История", "Семинар",2),
    (3, "Козлов", "Информатика", "Лекция",3),
    (2, "Иванов", "Химия", "Лабораторная",4),
    (3, "Петров", "Философия", "Семинар",5),
    (1, "Козлов", "Английский", "Практика",6),
    (2, "Сидоров", "География", "Лекция",7),
    (3, "Иванов", "Экономика", "Семинар",8),
    (1, "Петров", "Программирование", "Лабораторная",9),
    (2, "Козлов", "Биология", "Лекция",10),
    (3, "Сидоров", "Психология", "Семинар",11),
    (1, "Иванов", "Статистика", "Практика",12),
    (2, "Петров", "Социология", "Лекция",13),
    (3, "Козлов", "Маркетинг", "Семинар",14),
    (3, "Козлов", "Маркетинг", "Семинар",15),
    (3, "Козлов", "Маркетинг", "Семинар",16),
    (3, "Козлов", "Маркетинг", "Семинар",17),
    (3, "Козлов", "Маркетинг", "Семинар",18),
    (3, "Козлов", "Маркетинг", "Семинар",19),
]

TIME_SLOTS = ['8:00 - 9:30','9:40 - 11:10','11:20 - 12:50','13:20 - 14:50','15:00 - 16:30','16:40 - 18:10','18:20 - 19:50','20:00 - 21:30']
AUDITORIUMS = ['109','119а','119б','210','312','317','408','416']
#set_auditories(AUDITORIUMS)
#set_num_times(len(TIME_SLOTS))
#set_num_days(10)


def load_shedule(shedule, day):
    for alias in pygui.get_aliases():
        if alias.startswith('shedule_'):
            pygui.delete_item(alias,children_only=True)
    for shedule_info in sorted(shedule, key = lambda x:x[0]):
        day_number, time_slot, auditory, subject, is_lecture,teacher, group = shedule_info
        if day_number == day:
            pygui.add_text(group.name,parent = f'shedule_{TIME_SLOTS[time_slot]}_{auditory.name}',color=[255,0,0] if is_lecture else [0,255,0])
            pygui.add_text(teacher.name,parent = f'shedule_{TIME_SLOTS[time_slot]}_{auditory.name}',color=[255,0,0] if is_lecture else [0,255,0])
            pygui.add_text(subject.name,parent = f'shedule_{TIME_SLOTS[time_slot]}_{auditory.name}',color=[255,0,0] if is_lecture else [0,255,0])


def choose_date(sender, app_data, user_data):
    shedule = user_data
    date = pygui.get_value(sender)
    dt = datetime.date(date['year'] + 1900,month = date['month'] + 1, day = date['month_day'])
    load_shedule(shedule,(dt - datetime.datetime.now().date()).days)


with pygui.window(label = "Add/Edit", tag = "Add/Edit", modal= True, show = False, autosize=True, pos = (200,200)):
    pass

with pygui.window(tag = "Shedule"):
    reload_database()
#                load_shedule(shedule,0)
#                    date = (datetime.datetime.now() + datetime.timedelta(days=day_number)).date()
#                    if f'{date}_shedule' not in pygui.get_aliases():
#                        with pygui.tab(label = f'{date}',tag=f'{date}_shedule'):
#                            pass
                    
            

#pygui.bind_item_handler_registry(config.program_name, "test handler")

#    pygui.add_colormap(colors=[[255,0,0,255],[0,255,0,255]], tag = "test_colormap", qualitative=False)

pygui.create_viewport(title="Shedule", width=1800, height=900,resizable = False)



#dpg_dnd.set_drop(drop)

pygui.setup_dearpygui()
pygui.show_viewport()
pygui.set_primary_window("Shedule", True)
pygui.start_dearpygui()

pygui.destroy_context()
