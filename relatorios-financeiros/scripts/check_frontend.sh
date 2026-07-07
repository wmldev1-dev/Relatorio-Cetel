docker compose exec frontend bash -lc '
pwd
ls -R frontend
python -m compileall frontend
find frontend -type f -printf "%TY-%Tm-%Td %TH:%TM:%TS %p\n" | sort
streamlit --version
python --version
'
