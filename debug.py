import keyboard
count=0
def test():
    print("Hotkey pressed:", keyboard.get_hotkey_name())
    global count
    count+=1
    if count==3:
        keyboard.remove_hotkey(rec_hot_key)
#handler = keyboard.on_press_key("maiusc+r", test)
rec_hot_key=keyboard.add_hotkey('ctrl+r', test)
while True:
    keyboard.wait()
    
    
