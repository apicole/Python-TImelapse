#!/usr/bin/python3  - Timelapse ou 3DLapse selon OP_TIMELAPSE (Interrupteur sur BOUTTON_PIN)
import sys, os, keyboard, time, requests, socket, RPi.GPIO, gpiozero, gpiozero
from picamera2 import Picamera2             # Alternativement >>  from picamera import PiCamera + commenter camera.set_controls
 
RPi.GPIO.setmode(RPi.GPIO.BCM)              # GPIO en mode BCM
BOUTTON_PIN     = 27                        # PIN 27 est un bouton, ou une LED
button          = gpiozero.Button(str(BOUTTON_PIN))
RPi.GPIO.setup(BOUTTON_PIN, RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_UP)
OP_TIMELAPSE   = RPi.GPIO.input(BOUTTON_PIN)# Teste l'etat du GPIO 27. Si contact alors OP_TIMELAPSE = False
if len(sys.argv) > 1:
    if ("3d" or "3dlapse"  ) in sys.argv[1].lower(): OP_TIMELAPSE = 0
    if ("tl" or "timelapse") in sys.argv[1].lower(): OP_TIMELAPSE = 1 
camphotos,reminderID,camdelay = 0, 0, 2     # Initialise le compteur et intervalle de temps entre chaque photo ( <> 1 seconde pour temps de snapshot !)
start_programme = time.time()               # Pour affecter start_programme a il y a 80 : start_programme = time.time() - 80 * 60
for dossiers in range(1, 9999):             # Test incrementalement sur 4 chiffres, les dossiers pour trouver le prochain numero inexistant
    APPDIR = '/home/pi/Pictures/' + str(dossiers).zfill(4)
    if not os.path.exists(APPDIR):
        break
os.makedirs(APPDIR)                         # Cree le dossier dans APPDIR = /home/pi/Pictures/####

def log2file(text,ntfy=False,ntags="+1"):   # Enregistre les logs dans un fichier texte, et optionellement les partage sur notify si Internet est joignable
    with open(APPDIR+"/"+time.strftime("%Y%m%d")+"_Timelapse.log", 'a') as f:
        print (time.strftime("%Y-%m-%d %H:%M:%S") + " - " + text)  # Affiche en console
        f.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} - {text}\n')# Log dans le fichier
    f.close()
    if (ntfy):
        if (is_connected):                  # requests.post("https://ntfy.sh/mynameisbondjamesbond",data=nData,headers={"Title": nTitle,"Priority": nPrio,"Tags": nTags})
            requests.post("https://ntfy.sh/mynameisbondjamesbond",data=text,headers={"Title": sys.argv[0]+"@" + socket.gethostname(),"Priority": "urgent","Tags": ntags}) 
def is_connected():                         # Evalue si Internet est joignable
    try:
        socket.create_connection(("1.1.1.1", 53))
        return True
    except OSError:
        pass
    return False
def notify_pic(nFile,ntags="+1",nMode="Lapse"):           # Partage le fichier sur notify si Internet est joignable, parametre du tag par defaut : +1
    if (is_connected):
        if os.path.exists(nFile):
            if (int((time.time() - start_programme)/60)<60) : requests.put("https://ntfy.sh/mynameisbondjamesbond", data=open(str(nFile), 'rb'), headers={"Title": sys.argv[0]+"#"+nMode+"@" + socket.gethostname(),"Tags": ntags, "Filename": str(nFile) + " apres " + str((int((time.time() - start_programme)/60))) + " min"})
            else: requests.put("https://ntfy.sh/mynameisbondjamesbond", data=open(str(nFile), 'rb'), headers={"Title":  sys.argv[0]+"#"+nMode+"@" + socket.gethostname(),"Tags": ntags, "Filename": str(nFile) + " apres " + str(int((time.time() - start_programme)/3600)) + "h et " + str(int(((time.time() - start_programme) % 3600)/ 60))+ " min"})
def testFocus(tfmin=50, tfmax=1000, tfincrements=50):  # Fonction utilisee que pour regler l'auto focus (100 = far; 250 = 100 cm ; 300 = 40 cm; 400 = 20cm)  :: testFocus (290,390,5)
    for lensposition in range(tfmin,tfmax,tfincrements):
        camera.set_controls({"AfMode": 0, "LensPosition": lensposition})
        print ("tfmin:"+ str(tfmin)+ " ;tfmax:"+str(tfmax)+ ";increment"+ str(tfincrements)+ ";position:"+ str(lensposition)+  "/"+ str(tfmax))
        time.sleep(3)
        camera.capture_file(APPDIR+"image_"+str(lensposition)+".jpg")
def get_free_space_percent():               # Fonction retournant l'espace disque restant en pourcentage
    statvfs = os.statvfs("/")
    free = statvfs.f_frsize * statvfs.f_bavail
    total = statvfs.f_frsize * statvfs.f_blocks
    return (free / total) * 100
def shutdown():                             # Notification d'extinction via log, notify, LED, pendant 60 secondes avant arret
    log2file(" >  Extinction dans 60 sec.",True,"no_entry")
    if OP_TIMELAPSE: RPi.GPIO.output(BOUTTON_PIN, RPi.GPIO.HIGH) # Si nous sommes en Timelapse uniquement, allumage de la LED
    camera.stop()
    camera.close() 
    time.sleep(60)
    os.system("sudo shutdown -h now 'Arret du systeme par script'") # Extinction par commande shutdown
def MyTimeLapse(tlminutes):                 # Fonction principale pour le Timelapse (argument = temps en minutes)
    global camphotos, camdelay              # Recupere les valeurs des variables prealablement definies
    camera.capture_file(APPDIR + "/image000000.jpg".format(camphotos))
    numphotos = int((tlminutes*60)/camdelay-1)# Nombre de photos totales : (temps en minute * 60)/intervalle
    log2file("MyTimeLapse " + str(camwidth) + " x "+ str(camheight) +" chaque " + str(camdelay) + "sec pendant "+ str(tlminutes) +" min ("+str(numphotos)+" photos) | Disque:"+ str(round(get_free_space_percent()))  +"% libre | Internet:" + str(is_connected()))
    notify_pic(APPDIR + "/image000000.jpg".format(camphotos),"heavy_check_mark","MyTimeLapse")
    try:
        while camphotos < numphotos:
            camphotos += 1                  # Incremente la variable camphotos = nombre de photos
            if os.path.exists (APPDIR + "/STOP") or os.path.exists (APPDIR + "/END"): camphotos = numphotos
            RPi.GPIO.output(BOUTTON_PIN, RPi.GPIO.HIGH)  # Allume la LED qui est sur GPIO BOUTTON_PIN
            camera.capture_file(APPDIR + "/image{0:06d}.jpg".format(camphotos))
            RPi.GPIO.output(BOUTTON_PIN, RPi.GPIO.LOW)   # Eteint la LED qui est sur GPIO BOUTTON_PIN
            time.sleep(camdelay-1)
            if camphotos % 150 == 0:        # Toutes les 150 photos, log avancement, envoie la photo sur ntfy et vérifie l'espace disque
                notify_pic(APPDIR + "/image{0:06d}.jpg".format(camphotos),"+1","MyTimeLapse")  
                if (round(get_free_space_percent())<4): # Espace disque restant Inferieur a 4 pourcent !!
                    log2file(" > Stockage presque plein: " + str(round(get_free_space_percent()))+ "% restant > " + str(camphotos) + " / "+ str(numphotos) + " ~ "+ str(round(((numphotos -camphotos) * (camdelay-1)) /60))+ " min.",True,"rotating_light")
                else: log2file(" > " + str(camwidth) + " x " + str(camheight) + " > " + str(camphotos) + " / "+ str(numphotos) + " ~ "+ str(round(((numphotos -camphotos) * (camdelay-1)) /60))+ " min.")
    except KeyboardInterrupt:
        print ("Interruption Clavier")
        pass
    log2file("Fin: " + str(camphotos) + "/"+str(numphotos) + " >> ffmpeg -r 25 -f image2 -i image%6d.jpg -vcodec libx264 -crf 25 -pix_fmt yuv420p "+time.strftime("%Y%m%d_%Hh%Mm%S")+".mp4")
    shutdown()
def My3dLapse():
    global camphotos, start_time
    start_time = time.time()                # Nouvelle valeur de start_time pour compter le temps par niveau (trop long => alertes)
    reminderID = 0                          # Initialise la variable reminderID = nombre de rappels
    camphotos += 1                          # Incremente la variable camphotos = nombre de photos
    camera.capture_file(APPDIR + "/image{0:06d}.jpg".format(camphotos))
    if camphotos % 50 == 0:                 # Toutes les 50 photos, notifie de l'avancement dans le fichier de log
        log2file(" > " + str(camwidth) + " x " + str(camheight) + " > " + str(camphotos)+ " Snapshots")
        if camphotos % 100 == 0:            # Toutes les 100 photos, envoie la photo sur ntfy
            notify_pic(APPDIR + "/image{0:06d}.jpg".format(camphotos),"+1","My3DLapse")  

camera = Picamera2()
if OP_TIMELAPSE:
    RPi.GPIO.setup(BOUTTON_PIN, RPi.GPIO.OUT)
    RPi.GPIO.output(BOUTTON_PIN, RPi.GPIO.HIGH)  # Allume la LED qui est sur GPIO BOUTTON_PIN
    camwidth, camheight = 2560, 1440        # UHD4K:3840x2160 | QHD2K:2560x1440  |FHD1080p:1920x1080 | HD720:1280x720
    camera.set_controls({"AfMode": 2 ,"AfTrigger": 0}) # AutoFocus continu
else:
    camwidth, camheight = 1920, 1080        # UHD4K:3840x2160 | QHD2K:2560x1440  |FHD1080p:1920x1080 | HD720:1280x720
    camera.set_controls({"AfMode": 0, "LensPosition": 315})  # AutoFocus fixe;  100 = far; 250 = 100 cm ; 300 = 40 cm; 400 = 20cm
camera_config = camera.create_still_configuration(main={"size": (camwidth, camheight)}, lores={"size": (320, 240)}, display="lores")
camera.configure(camera_config)
camera.start()
if (round(get_free_space_percent())<10): log2file(" > Stockage presque plein: " + str(round(get_free_space_percent()))+ "% restant !",True,"rotating_light")

if OP_TIMELAPSE: MyTimeLapse(180)            # Temps en minutes du Timelapse : 1h = 60 min , 2h = 120 min , 3h = 180 min , 4h = 240 min 
else:
    log2file("My3dLapse " + str(camwidth) + " x "+ str(camheight) + " | Disque:"+ str(round(get_free_space_percent())) + "% libre | Internet:"  + str(is_connected()))
    camera.capture_file(APPDIR + "/image000000.jpg".format(camphotos))
    notify_pic(APPDIR + "/image000000.jpg".format(camphotos),"heavy_check_mark","My3dLapse")  
    start_time = time.time()                # Nouvelle valeur de start_time pour compter le temps par niveau (trop long => alertes)
    button.when_released = My3dLapse        # Execution de la fonction My3dLapse "when_released" au lacher du bouton GPIO 27 aurait pu etre "when_pressed"
    while True:
        if time.time() - start_time > 60:   # 1 minute 
            reminderID += 1                 # Incremente la variable reminderID = nombre de rappels
            log2file ("60 secondes sans nouveau layer (rappel: " + str(reminderID) + "x)", True)
            start_time = time.time()        # Nouvelle valeur de start_time pour compter le temps par niveau (trop long => alertes)
        if (reminderID > 7):                # Apres 7 rappels effectifs => extinction
            shutdown()
