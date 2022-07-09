import glob, os, re 
import numpy as np
import pandas as pd
from pydub import AudioSegment
import tqdm

def dataframe_weeks():
    groups = { 'historia' : {'prefix' : 'sound_ciclo1_ciclo1_historia'},
            'latim' : {'prefix' : 'sound_ciclo1_ciclo1_latim'}, 
            'matematica' : {'prefix' : 'sound_matematica_matematica'}
            }
    nweeks = 24 # number of weeks of the ciclo weeks : 24
    weeks = []

    def get_weeknumbers(file, prefix):
        """ week number or numbers """
        file = file[:-4] # drop mp3 
        file = file.replace(prefix,'')   
        if 'e' in file: 
            file = file.replace('e', '_')     
        return re.findall('\d{1,}', file)

    for n in range(nweeks):
        #if os.path.isfile('audio_week_'+str(nweek)):       
        weeks.append({ k : None for k in groups }) # add group names
        for group in groups: 
            weeks[n][group] = [ f for f in glob.glob(groups[group]['prefix']+"*") 
                        if str(n+1) in get_weeknumbers(f, groups[group]['prefix']) ]   

    # sound_linha_tempo_ + 'era_antigos_imperios' ...
    timeline_audios = ['era_antigos_imperios', 'idade_media', 'exploradores', 'era_iluminismo', 'era_progressiva', 'presidentes'] 

    timeline = pd.DataFrame(index=np.arange(1,25), columns=['beg', 'end', 'audio1', 'audio2'])

    timeline.loc[1:7,   ['audio1', 'audio2']] = ['era_antigos_imperios',  None]  #[1-7]: 1 (7)
    timeline.loc[8,     ['audio1', 'audio2']] = ['era_antigos_imperios',  'idade_media']  # 8 : 1-2 (1)
    timeline.loc[9:12,  ['audio1', 'audio2']] = ['idade_media',  None]  #[9-12] : 2 (4)
    timeline.loc[13:14, ['audio1', 'audio2']] = ['exploradores', None]
    timeline.loc[15,    ['audio1', 'audio2']] = ['exploradores', 'era_iluminismo']  #15 : 3-4 (1)
    timeline.loc[16:19, ['audio1', 'audio2']] = ['era_iluminismo', None] #[16-19] : 4 (4)
    timeline.loc[20,    ['audio1', 'audio2']] = ['era_iluminismo', 'era_progressiva']  #20 :  4-5 (1)
    timeline.loc[21:23, ['audio1', 'audio2']] = ['era_progressiva', None] #23 : 5 (3)
    timeline.loc[24,    ['audio1', 'audio2']] = ['presidentes', None]  #24 : 6

    # cuts in seconds per audio file
    cuts = {
        'era_antigos_imperios' : [np.nan, 33, 51, 1*60+17, 1*60+40, 2*60+8, 2*60+33, 3*60+4], 
        'idade_media' : [27, 1*60+5, 1*60+35, 1*60+57, 2*60+27],   # 8:
        'exploradores' : [np.nan, 46, 1*60+13], # 13: ^exploradores
        'era_iluminismo' : [10, 39, 1*60+16, 1*60+49, 2*60+20],  # 15: ^iluminismo
        'era_progressiva' : [43, 1*60+18, 1*60+55, np.nan], # 20: ^ progressista - audio 'progressiva'
        'presidentes' : [np.nan, np.nan]  # 24: ^ presidentes 
        }
    shift = 1
    def begend(times):
        return  [ [times[i-1]-shift, times[i]+shift] for i in range(1,len(times))] # 1 second before and after

    # cuts in seconds per audio file
    timeline.loc[1:7,   ['beg', 'end']] = begend(cuts['era_antigos_imperios'])
    timeline.loc[8,     ['beg', 'end']] = cuts['era_antigos_imperios'][-1]-shift,cuts['idade_media'][0]+shift
    timeline.loc[9:12,  ['beg', 'end']] = begend(cuts['idade_media'])
    timeline.loc[13:14, ['beg', 'end']] = begend(cuts['exploradores'])
    timeline.loc[15,    ['beg', 'end']] = cuts['exploradores'][-1]-shift,cuts['era_iluminismo'][0]+shift
    timeline.loc[16:19, ['beg', 'end']] = begend(cuts['era_iluminismo'])
    timeline.loc[20,    ['beg', 'end']] = cuts['era_iluminismo'][-1]-shift,cuts['era_progressiva'][0]+shift
    timeline.loc[21:23, ['beg', 'end']] = begend(cuts['era_progressiva'])
    timeline.loc[24,    ['beg', 'end']] = cuts['presidentes']
    timeline.loc[:, ['beg', 'end']] = timeline.loc[:, ['beg', 'end']]*1000 # to ms 

    dfweeks = timeline.join(pd.DataFrame(weeks, index=range(1,25)), how='outer')
    return dfweeks

def create_audios(dfweeks):
    for n, week in tqdm.tqdm(dfweeks.iterrows(), total=24):
        audios = []
        repeats = [2, 2, 4] # repeat times for each subject (due sings 3x, 3x, 2x) = total (6, 6, 8) = wanted 7 so almost ok
        #repeats = [1, 1, 1]
        for subject, repeat in zip(['historia', 'latim', 'matematica'], repeats):    
            for file in week[subject]:
                audios += [ AudioSegment.from_mp3(file) for _ in range(repeat) ] # to make crossfase bellow
        # linha do tempo
        repeat = 7                   
        if not week['audio2'] : # only one source timeline audio    
            for _ in range(repeat): # to make crossfase bellow
                audio = AudioSegment.from_mp3('sound_linha_tempo_'+week['audio1']+'.mp3')
                beg, end = week[['beg', 'end']]   
                beg = 0. if np.isnan(beg) else beg
                audio_cutted = audio[beg:]
                if not np.isnan(end):
                    span = end-beg
                    audio_cutted = audio_cutted[:span]       
                audios += [ audio_cutted ]
            #print('doing week: ', n, ' audios: ', audios)
        else:
            for _ in range(repeat):
                p1, p2 = (AudioSegment.from_mp3('sound_linha_tempo_'+_+'.mp3') for _ in week[['audio1', 'audio2']] )
                beg, end = week[['beg', 'end']]     
                audio_cutted = p1[beg:-2000].append(p2[:end], crossfade=(2*1000)) # a lot of silence at the end/begin of each timeline file
                audios += [ audio_cutted ]
            #print('doing week: ', n, ' audios: ', audios)
        # shuffle audios to make it less boring
        # random.shuffle(audios) # dont't my wife doesn't like
        merged_audio = audios[0]
        silent_gap = AudioSegment.silent(duration=3*1000) # some seconds of silence to avoid overlaping crossfade on real audio
        for audio in audios[1:]:
            # We don't want an abrupt stop at the end, so let's do a 3 second crossfades
            merged_audio = merged_audio.append(silent_gap)
            merged_audio = merged_audio.append(audio, crossfade=(2*1000))
        # lets save it!
        if not os.path.exists(os.path.join(os.getcwd(), 'merged-audios')):
            os.mkdir("merged-audios")
        with open(os.path.join(os.getcwd(), "merged-audios", "cc_found_c1_wk_{:02}.mp3".format(n)), 'wb') as out_f:
            merged_audio.export(out_f, format='mp3')