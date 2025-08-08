pip install numpy librosa hmmlearn soundfile

[recognize.py]
import os
import numpy as np
import librosa
import soundfile as sf
from hmmlearn import hmm

# Конфигурация
TRAIN_DIR = 'train'
COMMANDS = ['yes', 'no']
N_COMPONENTS = 4  # състояния на HMM
N_MFCC = 13

def load_audio_features(path):
    y, sr = sf.read(path)
    if y.ndim > 1:
        y = y[:, 0]
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
    return mfcc.T  # (време, признаци)

def train_models():
    models = {}
    for cmd in COMMANDS:
        features = []
        cmd_dir = os.path.join(TRAIN_DIR, cmd)
        for fname in os.listdir(cmd_dir):
            if fname.endswith('.wav'):
                fpath = os.path.join(cmd_dir, fname)
                mfcc = load_audio_features(fpath)
                features.append(mfcc)

        X = np.vstack(features)
        lengths = [len(f) for f in features]

        model = hmm.GaussianHMM(n_components=N_COMPONENTS, covariance_type='diag', n_iter=100)
        model.fit(X, lengths)
        models[cmd] = model
        print(f"✅ Обучен модел за '{cmd}' ({len(features)} примера)")

    return models

def recognize(models, test_path):
    test_mfcc = load_audio_features(test_path)
    scores = {}
    for cmd, model in models.items():
        try:
            score = model.score(test_mfcc)
            scores[cmd] = score
        except:
            scores[cmd] = float('-inf')

    best_cmd = max(scores, key=scores.get)
    print("\n🎧 Резултати:")
    for cmd, score in scores.items():
        print(f"  {cmd}: {score:.2f}")
    print(f"\n➡️ Разпознато: {best_cmd.upper()}")

if __name__ == '__main__':
    print("🎙️ Обучение...")
    models = train_models()
    print("\n🧪 Тестване върху файл: test/test.wav")
    recognize(models, "test/test.wav")
[/recognize.py]

mkdir -p train/yes train/no test

sudo apt update
sudo apt install alsa-utils

arecord -D plughw:0,0 -f cd -t wav -d 2 -r 16000 -c 1 train/yes/yes1.wav
arecord -D plughw:0,0 -f cd -t wav -d 2 -r 16000 -c 1 train/yes/yes2.wav
arecord -D plughw:0,0 -f cd -t wav -d 2 -r 16000 -c 1 train/no/no1.wav
arecord -D plughw:0,0 -f cd -t wav -d 2 -r 16000 -c 1 train/no/no2.wav
arecord -D plughw:0,0 -f cd -t wav -d 2 -r 16000 -c 1 test/test.wav

python3 recognize.py

aplay train/yes/yes1.wav
