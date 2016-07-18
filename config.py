class CfgOptions():
    host = '192.168.10.40'
    port = 9998
    vlc = 'c:/Program Files (x86)/VideoLAN/VLC/vlc.exe'
    preset_remux = '#duplicate{dst=std{access=file,mux=ffmpeg{mux=flv},dst=-}}'

cfgoptions = CfgOptions()
