%define pref 	%{_prefix}
%define python 	/usr/bin/python2.3
%define pyver 	2.3
%define port  	GTK
%define lcport 	gtk
%define unicode 0
%define tarname wxPythonSrc
%define version 2.5.1.5
%define ver2    2.5
%define release 1
%define wxprefbase %{pref}/lib/wxPython
%define wxpref  %{wxprefbase}-%{version}
%define name    wxPython%{port}-py%{pyver}


# Should the builtin image and etc. libs be used, or system libs?
# Distro specific RPMs should probably set this to 0, generic ones
# should use 1
%define builtin_libs 1


# Should --enable-debug_flag be used in release builds?  Using it
# defines __WXDEBUG__ and gives us runtime diagnostics that are turned
# into Python exceptions starting with 2.3.4.  (So turning it on is a
# very helpful thing IMO and is recommended.)  The code is still
# compiled with optimization flags and such when this option is used,
# it simply turns on some extra code.
%define debug_flag 1


# build the name of the real wx-config from the port, flags, etc.
%define dbgflg %(if [ "%{debug_flag}" = "1" ]; then echo d; fi)
%define uniflg %(if [ "%{unicode}" = "1" ]; then echo u; fi)
%define DBGFLG %(if [ "%{debug_flag}" = "1" ]; then echo D; fi)
%define UNIFLG %(if [ "%{unicode}" = "1" ]; then echo U; fi)
%define wxconfigname %{wxpref}/bin/wx%{lcport}%{uniflg}%{dbgflg}-%{ver2}-config

# turn off the generation of debuginfo rpm  (RH9)
%define debug_package %{nil}

#----------------------------------------------------------------
Summary:   Cross platform GUI toolkit for Python using wx%{port}
Name:      %{name}
Version:   %{version}
Release:   %{release}
Source0:   %{tarname}-%{version}.tar.gz
License:   wx Library Licence, Version 3
URL:       http://wxPython.org/
Packager:  Robin Dunn <robin@alldunn.com>
Group:     Development/Python
BuildRoot: %{_tmppath}/%{name}-buildroot
Prefix:    %{pref}

Provides: wxPython  = %{version}
Provides: wxPython%{port}  = %{version}

# Provides: libwx_%{lcport}%{uniflg}%{dbgflg}-%{ver2}.so
# Provides: libwx_%{lcport}%{uniflg}%{dbgflg}-%{ver2}.so(WX%{port}%{UNIFLG}%{DBGFLG}_%{ver2})
# Provides: libwx_%{lcport}%{uniflg}%{dbgflg}_gl-%{ver2}.so
# Provides: libwx_%{lcport}%{uniflg}%{dbgflg}_gl-%{ver2}.so(WX%{port}%{UNIFLG}%{DBGFLG}_%{ver2})


# old wxPython packages
Obsoletes: wxPython wxPython%{port}


%description
wxPython is a GUI toolkit for Python that is a wrapper around the
wxWidgets C++ GUI library.  wxPython provides a large variety of
window types and controls, all implemented with a native look and feel
(and native runtime speed) on the platforms it is supported on.

This package is implemented using the %{port} port of wxWidgets, and
includes the wx%{port} shared libs and etc.


%package -n wxPython%{port}-devel
Summary: wxPython%{port} development files
Group: Development/Libraries
Requires: wxPython%{port} = %{version}


%description -n wxPython%{port}-devel
This packages contains the headers and etc. for building apps or
Python extension modules that use the same wx%{port} shared libraries
that wxPython uses.

#----------------------------------------------------------------
%prep
%setup -q -n %{tarname}-%{version}


#----------------------------------------------------------------
%build

WXDIR=`pwd`
mkdir bld
cd bld

# Configure, trying to reduce external dependencies
../configure --with-%{lcport} \
	--prefix=%{wxpref} \
	--disable-soname \
	--disable-monolithic \
	--enable-rpath=%{wxpref}/lib \
	--with-opengl \
%if %{unicode}
	--enable-gtk2 \
	--enable-unicode \
%endif
	--enable-geometry \
	--enable-optimise \
	--enable-sound 	--with-sdl \
	--enable-display \
%if %{debug_flag}
	--enable-debug_flag \
%endif
%if %{builtin_libs}
	--with-libjpeg=builtin \
	--with-libpng=builtin \
	--with-libtiff=builtin \
	--with-zlib=builtin \
%endif


# Build wxWidgets and some contrib libs
make 
make -C contrib/src/gizmos 
make -C contrib/src/ogl CXXFLAGS="-DwxUSE_DEPRECATED=0"
make -C contrib/src/stc
make -C contrib/src/xrc


# Now build wxPython
cd $WXDIR/wxPython
%{python} setup.py \
	NO_SCRIPTS=1 \
	WXPORT=%{lcport} \
	UNICODE=%{unicode} \
	WX_CONFIG="$WXDIR/bld/wx-config --prefix=$WXDIR --exec-prefix=$WXDIR/bld" \
	CONTRIBS_INC="$WXDIR/contrib/include" \
	build


# Build wxrc (XRC resource tool)
cd $WXDIR/bld/contrib/utils/wxrc
make
strip wxrc


#----------------------------------------------------------------
%install

WXDIR=`pwd`
cd bld

# Install wxWidgets and the contribs
make prefix=$RPM_BUILD_ROOT%{wxpref} install
make -C contrib/src/gizmos prefix=$RPM_BUILD_ROOT%{wxpref} install
make -C contrib/src/ogl CXXFLAGS="-DwxUSE_DEPRECATED=0" prefix=$RPM_BUILD_ROOT%{wxpref} install
make -C contrib/src/stc prefix=$RPM_BUILD_ROOT%{wxpref} install
make -C contrib/src/xrc prefix=$RPM_BUILD_ROOT%{wxpref} install


# install wxPython
cd $WXDIR/wxPython
%{python} setup.py \
	NO_SCRIPTS=1 \
	WXPORT=%{lcport} \
	UNICODE=%{unicode} \
	WX_CONFIG="$RPM_BUILD_ROOT%{wxpref}/bin/wx-config --prefix=$RPM_BUILD_ROOT%{wxpref}" \
	install \
	--root=$RPM_BUILD_ROOT


cd $WXDIR/wxPython


# Since I want this RPM to be as generic as possible I won't let
# distutils copy the scripts (NO_SCRIPTS=1 above) since it will mangle
# the #! line to use the real python pathname.  Since some distros
# install python 2.2 as python2 and others as python I can't let
# distutils do that otherwise the dependencies will be fouled up.
# Copy them manually instead, leaving the #!/bin/env line intact. 
# TODO: Should this be dependent on %{builtin_libs} or something like
# it?

mkdir -p $RPM_BUILD_ROOT%{pref}/bin
for s in \
	helpviewer \
	img2png \
	img2py \
	img2xpm \
	pyalacarte \
	pyalamode \
	pycrust \
	pywrap \
	pyshell \
	xrced; do
    cp scripts/$s $RPM_BUILD_ROOT%{pref}/bin
done


# Install wxrc
cp $WXDIR/bld/contrib/utils/wxrc/wxrc $RPM_BUILD_ROOT%{pref}/bin


# install KDE & GNOME menus
mkdir -p $RPM_BUILD_ROOT%{_datadir}/applnk/Development
mkdir -p $RPM_BUILD_ROOT%{_datadir}/applications
for d in distrib/*.desktop; do
	install -m 644 $d $RPM_BUILD_ROOT%{_datadir}/applnk/Development
	install -m 644 $d $RPM_BUILD_ROOT%{_datadir}/applications
done

# install KDE icons
mkdir -p $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/{16x16,32x32}/apps
mkdir -p $RPM_BUILD_ROOT%{_datadir}/pixmaps
install -m 644 wx/py/PyCrust_16.png $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/16x16/apps/PyCrust.png
install -m 644 wx/py/PyCrust_32.png $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/32x32/apps/PyCrust.png
install -m 644 wx/py/PyCrust_32.png $RPM_BUILD_ROOT%{_datadir}/pixmaps/PyCrust.png
install -m 644 wx/tools/XRCed/XRCed_16.png $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/16x16/apps/XRCed.png
install -m 644 wx/tools/XRCed/XRCed_32.png $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/32x32/apps/XRCed.png
install -m 644 wx/tools/XRCed/XRCed_32.png $RPM_BUILD_ROOT%{_datadir}/pixmaps/XRCed.png

# install Mandrake menu
mkdir -p $RPM_BUILD_ROOT/%{_libdir}/menu
cat > $RPM_BUILD_ROOT%{_libdir}/menu/%{name} <<EOF
?package(%{name}): \\
	command="%{_bindir}/pyshell" \\
	needs="X11" \\
	icon="PyCrust.png" \\
	section="Applications/Development/Tools" \\
	title="PyShell" \\
	longtitle="GUI Python Shell"
?package(%{name}): \\
	command="%{_bindir}/pycrust" \\
	needs="X11" \\
	icon="PyCrust.png" \\
	section="Applications/Development/Tools" \\
	title="PyCrust" \\
	longtitle="GUI Python Shell with Filling"
?package(%{name}): \\
	command="%{_bindir}/pyalamode" \\
	needs="X11" \\
	icon="PyCrust.png" \\
	section="Applications/Development/Tools" \\
	title="PyAlaMode" \\
	longtitle="GUI Python Shell with Filling and editor windows"
?package(%{name}): \\
	command="%{_bindir}/xrced" \\
	needs="X11" \\
	icon="XRCed.png" \\
	section="Applications/Development/Tools" \\
	title="XRCed" \\
	longtitle="wxPython XRC resource editor"
EOF


#----------------------------------------------------------------

%pre
if [ -e %{wxprefbase} ]; then
	# in case there are old dirs from an old install
	rm -r %{wxprefbase}
fi


%post
if [ ! -e %{wxprefbase} ]; then
	ln -s wxPython-%{version}  %{wxprefbase}
fi
# This is done on Mandrake to update its menus:
if [ -x /usr/bin/update-menus ]; then /usr/bin/update-menus || true ; fi


%postun
rm -f %{wxprefbase}
# This is done on Mandrake to update its menus:
if [ "$1" = "0" -a -x /usr/bin/update-menus ]; then /usr/bin/update-menus || true ; fi


#----------------------------------------------------------------
%clean
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT


#----------------------------------------------------------------

%files
%defattr(-,root,root)
%doc docs/preamble.txt docs/licence.txt docs/lgpl.txt docs/readme.txt docs/changes.txt
%doc wxPython/docs/*
%{_bindir}/*
%{_libdir}/python%{pyver}/site-packages/*
%dir %{wxpref}
%dir %{wxpref}/lib
%{wxpref}/lib/libwx*
%{wxpref}/share
%{_datadir}/applnk/Development/*
%{_datadir}/applications/*
%{_datadir}/icons/hicolor/*/apps/*
%{_datadir}/pixmaps/*
%{_libdir}/menu/*

##%{wxprefbase}


%files -n wxPython%{port}-devel
%defattr(-,root,root)
%{wxpref}/include
%{wxpref}/lib/wx
%{wxconfigname}
%{wxpref}/bin/wx-config

#----------------------------------------------------------------
# end of file
