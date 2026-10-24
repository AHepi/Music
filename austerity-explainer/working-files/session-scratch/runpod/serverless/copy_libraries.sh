#!/bin/bash
# What this does: run once on a storage machine. Copies the system libraries Blender needs (X11 pieces, the OpenGL/EGL loaders,
# Vulkan loader) from that machine into the store, so the plain Ubuntu image of the pay-per-second workers can run Blender.
# Graphics driver libraries are NOT copied: each worker's driver provides its own.
set -e
B=/workspace/blender
mkdir -p /workspace/sls/libs
{ ldd $B/blender; for f in $B/lib/*.so*; do ldd "$f" 2>/dev/null; done; } | awk '/=> \//{print $3}' | sort -u > /tmp/resolved.txt
for name in libEGL libGL libGLX libGLdispatch libOpenGL libX11 libX11-xcb libxcb libXau libXdmcp libbsd libmd libXext libXi libXfixes \
            libXrender libxkbcommon libXxf86vm libSM libICE libuuid libvulkan libwayland-client libwayland-egl libwayland-cursor libffi libdecor-0; do
  ls /usr/lib/x86_64-linux-gnu/${name}.so* 2>/dev/null >> /tmp/resolved.txt || true
done
grep -v -E '/(libc|libm|libpthread|libdl|librt|libutil|ld-linux-x86-64|libgcc_s|libstdc\+\+)\.so|nvidia|libcuda|libnv' /tmp/resolved.txt \
  | grep -v '^/workspace' | sort -u > /tmp/keep.txt
while read -r library; do cp -L "$library" /workspace/sls/libs/; done < /tmp/keep.txt
echo "copied $(ls /workspace/sls/libs | wc -l) libraries"; du -sh /workspace/sls/libs; ldd $B/blender | grep 'not found' || echo 'nothing missing on this machine'
