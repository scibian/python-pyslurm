%define modname pyslurm
Name:           python-pyslurm
Version:        23.2.2
Release:        1%{?dist}.edf
Summary:        A Python/Cython extension module to SLURM
License:        GPL-2.0
Group:          Development/Libraries/Python
Url:            http://www.gingergeeks.co.uk/pyslurm
Source0:        %{name}-%{version}.tar.gz
Patch0:         0001-backport-cython-0.28.1.patch
BuildRequires:  python3-Cython
BuildRequires:  python3-devel
BuildRequires:  slurm-devel >= 23, slurm-devel < 24
BuildRequires:  python3-setuptools
Requires:       slurm >= 23, slurm < 24

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
%doc COPYING.txt README.md
%{python3_sitearch}/%{modname}
%{python3_sitearch}/%{modname}-*-py%{python3_version}.egg-info

%changelog
* Wed Nov 29 2023 Mathieu Chouquet-Stringer <mathieu-externe.chouquet-stringer@edf.fr> 23.2.2-1.el8.edf
- New upstream release 23.2.2

* Wed Mar 15 2023 Rémi Palancher <remi-externe.palancher@edf.fr> 22.5.1-1.el8.edf
- New upstream release 22.5.1
- Add patch to backport to Cython 0.28.1
- Remove patch to support Slurm 21.08 merged upstream

* Mon Feb 7 2022 Rémi Palancher <remi-externe.palancher@edf.fr> 20.11~git20220207-1.el8.edf
- Import new upstream version 20.11~git20220207
- Support patch for mcs_label merged upstream
- Add patch to support Slurm 21.08

* Thu Nov 25 2021 Rémi Palancher <remi-externe.palancher@edf.fr>
- Some rework on RPM base name to match Fedora guidelines for Python libraries
- Add patch to convert node mcs_label from bytes to string

* Tue Feb 25 2020 Guillaume RANQUET <guillaume-externe.ranquet@edf.fr>
- Update spec for rhel8/python3
- Use pyslurm 20.02.2 from internal edf git repository while there's no official pyslurm release for slurm 20.02.2

* Sat Apr 27 2013 scorot@free.fr
- first package
