# VolumeViewer
3D Volume viewer for microscopy data

## Setup

```
conda env create -f environment.yml -p /path/on/big/drive/volumeviewer
conda activate /path/on/big/drive/volumeviewer
volumeviewer
```

The path passed to `-p` can be anywhere with enough disk space (e.g. a data drive rather than your home directory's default conda envs location).

### Prerequisites
- A GPU/driver supporting OpenGL 4.3 core profile.
- A real display available to the process (local desktop, `ssh -X`, or VNC). GLFW cannot open a window on a headless terminal session.
