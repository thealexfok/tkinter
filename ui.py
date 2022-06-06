from abc import ABC, abstractmethod
from tkinter import *
from enum import Flag, Enum


class LanguageType(Enum):
    ENGLISH = 0 ##ALL CAPS COZ OF CONSTANTS
    PIGLATIN = 1

class ElementType(Flag):
    NONE = 0
    HAS_TEXT = 1
    HAS_ACTION = 2
    HAS_IMAGE = 4
    IS_CONTAINER = 8

    

class UIElement(ABC):
    UILanguage = LanguageType.ENGLISH
    _Messages = {}

    def __init__(self,name = None):
        self.name = name
        self.type = ElementType.NONE
        self.owner = None
        self.side = None

    def GetType(self):
        return self.type
    
    @abstractmethod
    def __str__(self):
        pass

    @classmethod
    def SendMessage(cls,targetName,message):
        if targetName in cls._Messages:
            cls._Messages[targetName].append(message)
        else:
            cls._Messages[targetName] = [message]
    
    @classmethod
    def ProcessMessages(cls):
        for name, messageList in cls._Messages.items():
            for element in UIRoot._singleton.FindEachElementsByName(name):
                for message in messageList:
                    element._ProcessMessage(message)
        cls._Messages.clear()

    @abstractmethod
    def _Place(self):
        pass


class UIMessage:
    def __init__(self,newText=None,newImage=None):
        if newText is not None:
            self.newText = newText
        if newImage is not None:
            self.newImage = newImage

    def ButtonCallback(self, target):
        UIElement.SendMessage(target,self)

class I_Frame:
    def __init__(self,frame,forward):
        self.frame = frame
        if forward:
            self.index = 0
            self.dir = 1
        else:
            self.index = 1
            self.dir = -1

    def GetType(self):
        return self.type

    def __iter__(self):
        return self

    def __next__(self):
        if self.index >1 or self.index <0:
            raise StopIteration
        result = self.frame[self.index]
        self.index +=self.dir
        return result


class M_Text:
    def __init__(self,text):
        self.text = StringVar() ##string var is a class
        self.SetText(text)
    
    def SetText(self,text):
        if isinstance(text,dict):
            if UIElement.UILanguage in text:
                text = text[UIElement.UILanguage]
            else:
                text = ""
        self.text.set(text)



class UIFrame(UIElement):

    def __init__(self,root = None,name=None, **kwargs):
        UIElement.__init__(self,name= name)
        self.type = ElementType.IS_CONTAINER
        self.lst =[]
        self.root=root
        self.kwargs = kwargs
        if root is not None:
            self._Place(root)
            root.bind('<KeyPress>', UIFrame._Down)
            root.bind('<KeyRelease>', UIFrame._Up)
    
    def CopySelf(self, name = None, addToSameFrame=False, **override_args):
        newname = self.name if name is None else name
        newframe = UIFrame(name = newname, **self.kwargs)
        newframe.kwargs.update(override_args)
        if addToSameFrame:
            newframe.kwargs.pop("addToSameFrame", None)
            self.owner.Add(newframe, self.side)
        for element in self.lst:
            newframe.Add(element.CopySelf())
        return newframe

    @classmethod
    def _Down(cls,e):

        pass

    @classmethod
    def _Up(cls,e):

        pass

    def Add(self, item, side=LEFT, hide = False, **kwargs):
        item._Place(self.frame,push=side, **kwargs)
        self.lst.append(item)
        item.owner = self
        item.side = side
        if not hasattr(self, "frame"):
            item.kwargs = kwargs
            item.hide=hide
            return
        item._Place(self.frame,push = side, **kwargs)
        if hide:
            item._Hide()
    
    def FindFrameElementsByFrame(self,name):
        return [item for item in self.lst if item.name == name]
    
    def FindElementsByName(self,name):
        lst = []
        for item in self.lst:
            if item.name == name:
                lst.append(item)
            if isinstance(item,UIFrame):
                elm = item.FindElementsByName(name)
                lst.extend(elm)
        return lst

    def FindEachElementsByName(self,name):
        for item in self.lst:
            if item.name == name:
                yield item
            if isinstance(item,UIFrame):
                yield from item.FindElementsByName(name)

    def __iadd__(self,uiElement):
        if issubclass(type(uiElement),UIElement):
            self.Add(uiElement)
            return self
        return NotImplemented

    def _Place(self,frame,push =TOP,**kwargs):
        self.kwargs.update(kwargs)
        self.frame = Frame(frame,**self.kwargs)
        self.frame.pack(side =push)
        for i in self.lst:
            i._Place(self.frame, push=i.side, **i.kwargs)
            if i.hide:
                i._Hide()

    
    def __str__(self, tab = 0):
        r = "Frame\n"
        tab +=1
        for i in self.lst:
            for j in range(tab):
                r += "\t"
            if isinstance(i,UIFrame):
               r+= i.__str__(tab =tab)
            else:
                r += str(i) + "\n"
        return r
    
    def __len__(self):
        return len(self.lst)
    
    def __getitem__(self,key):
        if isinstance(key,int):
            if key >= len(self.lst) or key < -len(self.lst):
                raise IndexError
            return self.lst[key]
        raise TypeError
    
    def __iter__(self):
        return I_Frame(self, True)

    def __reversed__(self):
        return I_Frame(self, False)
    
    def ShowElements(self, name):
        for i in self.FindEachElementsByName(name):
            i._Show()
        
    def HideElements(self, name):
        for i in self.FindEachElementsByName(name):
            i._Hide()
    
    def _Show(self):
        self.frame.pack(side=self.side)
    
    def _Hide(self):
        self.frame.pack_forget()


class UIRoot(UIFrame):
    _singleton = None
    def __new__(cls,*args,**kwargs):
        if not cls._singleton:
            cls._singleton = super(UIRoot,cls).__new__(cls,*args,**kwargs)
        return cls._singleton

    def __init__(self,name="root",**kwargs):
        kwargs.pop("root", None)
        self.root=Tk()
        UIFrame.__init__(self,root=self.root,name=name,**kwargs)

    def _Update(self):
        UIElement.ProcessMessages()
        self.root.after(100, self._Update)

    def mainloop(self):
        self.root.after(100, self._Update)
        self.root.mainloop()

class UILabel(UIElement, M_Text):
    def __init__(self,text, name= None,**kwargs):
        UIElement.__init__(self,name=name)
        M_Text.__init__(self,text)
        self.type = ElementType.HAS_TEXT
        self.kwargs = kwargs

    def _Place(self,frame,push = TOP,**kwargs):
        self.kwargs.update(kwargs)
        self.kwargs.pop("textvariable", None)
        self.label = Label(frame,textvariable = self.text,**self.kwargs)
        self.label.pack(side=push)

    def CopySelf(self, text = "", name = None, addToSameFrame=False, **override_args):
        newtext = self.text.get() if text == "" or text is None else text
        newname = self.name if name is None else name
        newlabel = UILabel(text =newtext, name = newname, **self.kwargs)
        newlabel.kwargs.update(override_args)
        if addToSameFrame:
            newlabel.kwargs.pop("addToSameFrame", None)
            self.owner.Add(newlabel, self.side)
        return newlabel

    def __str__(self):
        return "Label: " + self.text.get()  
    
    def _Show(self):
        self.label.pack(side=self.side)
    
    def _Hide(self):
        self.label.pack_forget()
    
    def _ProcessMessage(self,message):
        if hasattr(message, "newText"):
            self.SetText(message.newText)

class UIButtonPair(UIElement):
    def __init__(self, action, data=None, name=None, text1="",\
                text2="",**kwargs):
        UIElement.__init__(self,name=name)
        self.type = ElementType.HAS_ACTION |ElementType.IS_CONTAINER
        self.text1 = text1
        self.text2 = text2
        self.action = action
        self.data = data
        self.kwargs = kwargs
        self.last_action = None

    def Button1Action(self, data): #callback
        self.last_action =1
        self.action(data)
    
    def Button2Action(self, data): #callback
        self.last_action =2
        self.action(data)
    
    def ButtonText1(self): #callback
        return self.text1

    def ButtonText2(self): #callback
        return self.text2

    
    def _Place(self,frame,push = TOP,**kwargs):
        self.kwargs.update(kwargs)
        self.kwargs.pop("textvariable", None)
        self.kwargs.pop("command", None)
        self.frame = UIFrame(**kwargs)
        self.frame._Place(frame, push=push, **kwargs)
        self.button1 = UIButton(action=self.Button1Action, data = self.data,
                                text = self.ButtonText1())
        self.button2 = UIButton(action=self.Button2Action, data = self.data,
                                text = self.ButtonText2())        
        self.frame.Add(self.button1, side = LEFT)
        self.frame.Add(self.button2, side = LEFT)
    
    def _Show(self):
        self.frame._Show()
    
    def _Hide(self):
        self.frame._Hide()
    
    def __str__(self):
        return str(self.frame)
    
    
    def _ProcessMessage(self,message):
        pass
    
class UIOKCancel(UIButtonPair):
    def __init__(self,action,data=None,name=None,hideElement=None, **kwargs):
        UIButtonPair.__init__(self,action,data=data,name=name,hideElement=True,\
                                text1="OK", text2="Cancel",**kwargs)
        self.hideElement = hideElement

    def _HideElement(self):
        if self.hideElement !=None:
            self.hideElement._Hide()
        else:
            self._Hide()

    def Button1Action(self, data):
        self.action(data)
        self._HideElement()

    def Button2Action(self, data):##data is filler parameter
        self._HideElement()


class UIImage(UIElement):
    _ImageDict = {}

    def __init__(self, path, name=None, **kwargs):
        UIElement.__init__(self,name=name)
        self.type = ElementType.HAS_IMAGE
        self.path = path
        self.kwargs=kwargs
        self._SetNowImage(path)

    def _SetNowImage(self, path):
        if path in UIImage._ImageDict:
            self.photo = UIImage._ImageDict[path]
        else:
            self.photo = PhotoImage(file=path)
            UIImage._ImageDict[path] = self.photo

    def _Place(self, frame,push=TOP,**kwargs):
        self.kwargs.update(kwargs)
        self.image = Canvas(frame, width = self.photo.width(), height = self.photo.height(),
            **self.kwargs)        
        self.image.pack(side = push)
        self.imageID = self.image.create_image(0, 0, anchor=NW, image=self.photo)
    
    def CopySelf(self, path = None, name = None, addToSameFrame=False, **override_args):
        newpath = self.path if path is None else path
        newname = self.name if name is None else name
        newimage = UIImage(path =newpath, name = newname, **self.kwargs)
        newimage.kwargs.update(override_args)
        if addToSameFrame:
            newimage.kwargs.pop("addToSameFrame", None)
            self.owner.Add(newimage, self.side)
        return newimage

    def _Show(self):
        self.image.pack(side=self.side)
    
    def _Hide(self):
        self.image.pack_forget()

    def __str__(self):
        return "Image: "+ self.path
    
    def SetImage(self,path):
        self._SetNowImage(path)
        self.image.config(width=self.photo.width(),height=self.photo.height())
        self.image.itemconfig(self.imageID,image=self.photo)

    def _ProcessMessage(self,message):
        if hasattr(message, "newImage"):
            self.SetImage(message.newImage)

    
class UIButton(UIElement, M_Text):
    def __init__(self, action, data =None, text = "", name =None, **kwargs):
        UIElement.__init__(self,name=name)
        M_Text.__init__(self,text)
        self.type = ElementType.HAS_TEXT | ElementType.HAS_ACTION
        self.kwargs = kwargs
        self.action = action
        self.data = data

    
    def CopySelf(self, action = None, data = None, text = "", name = None, addToSameFrame=False, **override_args):
        newaction = self.action if action is None else action
        newdata = self.data if data is None else data
        newtext = self.text.get() if text == "" or text is None else text
        newname = self.name if name is None else name
        newbutton = UIButton(newaction,data = newdata, text =newtext, name = newname, **self.kwargs)
        newbutton.kwargs.update(override_args)
        if addToSameFrame:
            newbutton.kwargs.pop("addToSameFrame", None)
            self.owner.Add(newbutton, self.side)
        return newbutton
    
    def _Place(self,frame,push = TOP,**kwargs):
        self.kwargs.update(kwargs)
        self.kwargs.pop("textvariable", None)
        self.kwargs.pop("command", None)
        self.button = Button(frame, textvariable = self.text, command=self._Command,**kwargs)
        self.button.pack(side = push)
    
    def _Command(self):
        self.action(self.data)

    def __str__(self):
        return "Button: " + self.text.get()
    
    def _Show(self):
        self.button.pack(side=self.side)
    
    def _Hide(self):
        self.button.pack_forget()
    
    def _ProcessMessage(self,message):
        if hasattr(message, "newText"):
            self.SetText(message.newText)


class UIFactory():
    ElementCreatorDict = {
        "root" : UIRoot,
        "frame" : UIFrame,
        "button" : UIButton,
        "label" : UILabel,
        "image" : UIImage
    }

    @classmethod
    def NewElement(cls, ui_element_name,*args,**kwargs):
        if ui_element_name in cls.ElementCreatorDict:
            return cls.ElementCreatorDict[ui_element_name](*args,**kwargs)


    
def _ElementLogWrapper(cls,func): 
    def wrapper(*args,**kwargs):
        print("Created " + cls.__name__)
        return func(*args, **kwargs)
    
    return wrapper(func)

_ElementLoggingOn = False
def TurnOnElementCreationLogging():
    global _ElementLoggingOn
    if not _ElementLoggingOn: ##wrapper can be stacked
        _ElementLoggingOn = True
        #UIElement.__init__ = _ElementLogWrapper(UIElement,UIElement.__init__)
        UIFrame.__init__ = _ElementLogWrapper(UIFrame,UIFrame.__init__)
        UILabel.__init__ = _ElementLogWrapper(UILabel,UILabel.__init__)
        UIButton.__init__ = _ElementLogWrapper(UIButton,UIButton.__init__)
