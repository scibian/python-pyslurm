%define modname pyslurm
Name:           python-pyslurm
Version:        20.02.2
Release:        1%{?dist}.edf
Summary:        A Python/Cython extension module to SLURM
License:        GPL-2.0
Group:          Development/Libraries/Python
Url:            http://www.gingergeeks.co.uk/pyslurm
Source0:        %{name}-%{version}.tar.gz
Patch0:         0001-Convert-mcs_label-bytes-string-if-defined.patch
BuildRequires:  python3-Cython
BuildRequires:  python3-devel
BuildRequires:  slurm-devel
BuildRequires:  python3-setuptools
Requires:       slurm

%description

%global _description %{expand:
PySLURM is a Python/Cython extension module to the Simple Linux Unified
Resource Manager (SLURM) API. SLURM is typically used on HPC clusters
such as those listed on the TOP500 but can used on the smallest to the
largest cluster.

The original and current implementation (1.X/2.x) of PySLURM was a thin
layer for the SLURM C function calls but this is currently being hidden
behind an object orientated interface.}

%description %_description

%package -n python3-pyslurm
Summary:        %{summary}

%description -n python3-pyslurm %_description

%prep
%setup -q
%patch0 -p1

%build
CFLAGS="%{optflags}" python3 setup.py build

%install
python3 setup.py install --prefix=%{_prefix} --root=%{buildroot}

%files -n python3-pyslurm
%defattr(-,root,root,0755)
%doc CONTRIBUTORS.rst COPYING.txt README.rst THANKS.rst
%{python3_sitearch}/%{modname}
%{python3_sitearch}/%{modname}-*-py%{python3_version}.egg-info

%changelog
* Thu Nov 25 2021 Rémi Palancher <remi-externe.palancher@edf.fr>
- Some rework on RPM base name to match Fedora guidelines for Python libraries
- Add patch to convert node mcs_label from bytes to string

* Tue Feb 25 2020 Guillaume RANQUET <guillaume-externe.ranquet@edf.fr>
- Update spec for rhel8/python3
- Use pyslurm 20.02.2 from internal edf git repository while there's no official pyslurm release for slurm 20.02.2

* Sat Apr 27 2013 scorot@free.fr
- first package
