# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import functools

import numpy as np
import scipy.io as sio
from scikits.audiolab import Sndfile, Format
from matplotlib.pyplot import *

import librosa
import dict_prior as dp

# <codecell>

specshow = functools.partial(imshow, cmap=cm.hot_r, aspect='auto', origin='lower', interpolation='nearest')

def logspec(X, amin=1e-10, dbdown=80):
    logX = 20 * np.log10(np.maximum(X, amin))
    return np.maximum(logX, logX.max() - dbdown)

# <codecell>

TIMIT_DIR = '../timit/train/'

# <codecell>

def load_timit(wav_dir):
    f = Sndfile(wav_dir, 'r')
    wav = f.read_frames(f.nframes)
    return wav

# <codecell>

def learn_prior(W, L, maxiter=50, seed=None):
    sfd = dp.SF_Dict(W, L=L, seed=seed)
    obj = []
    for i in xrange(maxiter):
        print 'ITERATION: {}'.format(i)
        sfd.vb_e()
        if sfd.vb_m():
            break
        obj.append(sfd.obj)
    return (sfd.U, sfd.gamma, sfd.alpha, obj)

def encode(W, U, gamma, alpha, seed=None):
    L, _ = U.shape
    sfd = dp.SF_Dict(W, L=L, seed=seed)
    sfd.U, sfd.gamma, sfd.alpha = U, gamma, alpha
    sfd.vb_e()
    return sfd.EA
    
def write_wav(w, filename, channels=1, samplerate=16000):
    f_out = Sndfile(filename, 'w', format=Format(), channels=channels, samplerate=samplerate)
    f_out.write_frames(w)
    f_out.close()
    pass

# <codecell>

reload(librosa)
import scipy.signal
n_fft = 1024
hop_length = 512
wav = load_timit(TIMIT_DIR + 'dr1/fcjf0/sa1.wav')
W_complex = librosa.stft(wav, n_fft=n_fft, hop_length=hop_length, window=scipy.signal.bartlett(n_fft))

# <codecell>

ww = librosa.istft(W_complex, n_fft=n_fft, hop_length=hop_length, window=scipy.signal.bartlett(n_fft))
write_wav(ww, 'test.wav')
write_wav(wav, 'sa1.wav')

# <codecell>

ratio = amax(ww) / amax(wav)
plot(ww - ratio * wav[:ww.size])

# <codecell>

specshow(logspec(np.abs(W_complex)))
colorbar() 
pass

# <codecell>

threshold = 0.005
old_obj = -np.inf
L = 10
maxiter = 50
sfd = dp.SF_Dict(np.abs(W_complex.T), L=L, seed=98765)
obj = []
for i in xrange(maxiter):
    sfd.vb_e(disp=1)
    if sfd.vb_m(disp=1):
        break
    obj.append(sfd.obj)
    improvement = (sfd.obj - old_obj) / abs(sfd.obj)
    print 'After ITERATION: {}\tImprovement: {:.4f}'.format(i, improvement)
    if (sfd.obj - old_obj) / abs(sfd.obj) < threshold:
        break
    old_obj = sfd.obj

# <codecell>

plot(obj)
print diff(obj) / obj[1:]

# <codecell>

specshow(sfd.U)
colorbar()

# <codecell>

for l in xrange(L):
    figure(l)
    plot(np.exp(sfd.U[l]))
tight_layout()
pass

# <codecell>

figure()
plot(sfd.alpha)
figure()
plot(np.sqrt(1./sfd.gamma))
pass

# <codecell>

sf_encoder = dp.SF_Dict(np.abs(W_complex.T), L=L, seed=98765)
sf_encoder.U, sf_encoder.gamma, sf_encoder.alpha = sfd.U, sfd.gamma, sfd.alpha
sf_encoder.vb_e()
A = sf_encoder.EA

# <codecell>

W_rec_amp = np.exp(np.dot(A, sfd.U)).T
W_rec = W_rec_amp * np.exp(1j * np.angle(W_complex))

# <codecell>

subplot(211)
specshow(logspec(np.abs(W_complex)))
colorbar()
subplot(212)
specshow(logspec(W_rec_amp))
colorbar()
pass

# <codecell>

w_rec = librosa.istft(W_rec, n_fft=n_fft, hop_length=hop_length)
write_wav(w_rec, 'rec_fit.wav')
w_rec_org = librosa.istft(W_complex, n_fft=n_fft, hop_length=hop_length)
write_wav(w_rec_org, 'rec_org.wav')

