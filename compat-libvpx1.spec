%global majorver 1
%global minorver 3
%global tinyver  0

Name:			compat-libvpx1
Summary:		Compat package with libvpx libraries
Version:		%{majorver}.%{minorver}.%{tinyver}
%global soversion	%{version}
Release:		4%{?dist}
License:		BSD
Group:			System Environment/Libraries
Source0:		http://webm.googlecode.com/files/libvpx-v%{version}.tar.bz2
# Thanks to debian.
Source2:		libvpx.ver
Patch0:			Bug-fix-in-ssse3-quantize-function.patch
# Fix the build with gcc 5
# http://launchpadlibrarian.net/199480430/libvpx_1.3.0-3_1.3.0-3ubuntu1.diff.gz
Patch1:			libvpx-v1.3.0-gcc-5.patch
# Allow setting a size-limit to fix CVE-2015-1258
Patch2:			libvpx-1.3.0-CVE-2015-1258.patch
URL:			http://www.webmproject.org/code/
%ifarch %{ix86} x86_64
BuildRequires:		yasm
%endif
BuildRequires:		doxygen, php-cli

# Explicitly conflict with older libvpx packages that ship libraries
# with the same soname as this compat package
Conflicts: libvpx < 1.4.0

%description
Compatibility package with libvpx libraries ABI version 1.

%prep
%setup -q -n libvpx-v%{version}
%patch0 -p1 -b .patch0
%patch1 -p1 -b .gcc-5
%patch2 -p1 -b .CVE-2015-1258

%build
%ifarch %{ix86}
%global vpxtarget x86-linux-gcc
%else
%ifarch	x86_64
%global	vpxtarget x86_64-linux-gcc
%else
%ifarch armv7hl
%global vpxtarget armv7-linux-gcc
%else
%global vpxtarget generic-gnu
%endif
%endif
%endif

# The configure script will reject the shared flag on the generic target
# This means we need to fall back to the manual creation we did before. :P
%if "%{vpxtarget}" == "generic-gnu"
%global generic_target 1
%else
%global	generic_target 0
%endif

%ifarch armv7hl
CROSS=armv7hl-redhat-linux-gnueabi- CHOST=armv7hl-redhat-linux-gnueabi-hardfloat ./configure \
%else
./configure --target=%{vpxtarget} \
%endif
--enable-pic --disable-install-srcs \
%if ! %{generic_target}
--enable-shared \
%endif
--prefix=%{_prefix} --libdir=%{_libdir} --size-limit=16384x16384

# Hack our optflags in.
sed -i "s|-O3|%{optflags}|g" libs-%{vpxtarget}.mk
sed -i "s|-O3|%{optflags}|g" examples-%{vpxtarget}.mk
sed -i "s|-O3|%{optflags}|g" docs-%{vpxtarget}.mk

%ifarch armv7hl
#hackety hack hack
sed -i "s|AR=armv7hl-redhat-linux-gnueabi-ar|AR=ar|g" libs-%{vpxtarget}.mk
sed -i "s|AR=armv7hl-redhat-linux-gnueabi-ar|AR=ar|g" examples-%{vpxtarget}.mk
sed -i "s|AR=armv7hl-redhat-linux-gnueabi-ar|AR=ar|g" docs-%{vpxtarget}.mk

sed -i "s|AS=armv7hl-redhat-linux-gnueabi-as|AS=as|g" libs-%{vpxtarget}.mk
sed -i "s|AS=armv7hl-redhat-linux-gnueabi-as|AS=as|g" examples-%{vpxtarget}.mk
sed -i "s|AS=armv7hl-redhat-linux-gnueabi-as|AS=as|g" docs-%{vpxtarget}.mk

sed -i "s|NM=armv7hl-redhat-linux-gnueabi-nm|NM=nm|g" libs-%{vpxtarget}.mk
sed -i "s|NM=armv7hl-redhat-linux-gnueabi-nm|NM=nm|g" examples-%{vpxtarget}.mk
sed -i "s|NM=armv7hl-redhat-linux-gnueabi-nm|NM=nm|g" docs-%{vpxtarget}.mk
%endif

make %{?_smp_mflags} verbose=true target=libs

%if %{generic_target}
# Manual shared library creation
mkdir tmp
cd tmp
ar x ../libvpx_g.a
cd ..
gcc -fPIC -shared -pthread -lm -Wl,--no-undefined -Wl,-soname,libvpx.so.%{majorver} -Wl,--version-script,%{SOURCE2} -Wl,-z,noexecstack -o libvpx.so.%{soversion} tmp/*.o
rm -rf tmp
%endif

# Temporarily dance the static libs out of the way
mv libvpx.a libNOTvpx.a
mv libvpx_g.a libNOTvpx_g.a

# We need to do this so the examples can link against it.
ln -sf libvpx.so.%{soversion} libvpx.so

make %{?_smp_mflags} verbose=true target=examples CONFIG_SHARED=1
make %{?_smp_mflags} verbose=true target=docs

# Put them back so the install doesn't fail
mv libNOTvpx.a libvpx.a
mv libNOTvpx_g.a libvpx_g.a

%install
make DIST_DIR=%{buildroot}%{_prefix} dist

# Simpler to label the dir as %%doc.
mv %{buildroot}/usr/docs doc/

%if %{generic_target}
install -p libvpx.so.%{soversion} %{buildroot}%{_libdir}
pushd %{buildroot}%{_libdir}
ln -sf libvpx.so.%{soversion} libvpx.so
ln -sf libvpx.so.%{soversion} libvpx.so.%{majorver}
ln -sf libvpx.so.%{soversion} libvpx.so.%{majorver}.%{minorver}
popd
%endif

pushd %{buildroot}
# Stuff we don't need.
rm -rf usr/build/ usr/md5sums.txt usr/lib*/*.a usr/CHANGELOG usr/README
popd

# Remove files that aren't needed for the compat package
rm -rf %{buildroot}%{_bindir}
rm -rf %{buildroot}%{_includedir}
rm -rf %{buildroot}%{_libdir}/*.so
rm -rf %{buildroot}%{_libdir}/pkgconfig/

%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig

%files
%license LICENSE
%{_libdir}/libvpx.so.*

%changelog
* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1.3.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Wed Sep 16 2015 Kalev Lember <klember@redhat.com> - 1.3.0-3
- Set --size-limit=16384x16384 to fix CVE-2015-1258

* Mon Jul 27 2015 Kalev Lember <klember@redhat.com> - 1.3.0-2
- Package review fixes (#1225648)
- Update URL
- Escape a commented out macro
- Avoid mixed buildroot/RPM_BUILD_ROOT use

* Wed May 27 2015 Kalev Lember <kalevlember@gmail.com> - 1.3.0-1
- libvpx ABI version 1 compatibility package (#1225648)
