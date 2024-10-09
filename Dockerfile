# Use uma imagem base oficial do Python
FROM python:3.12.6-alpine

# Crie um diretório de trabalho
WORKDIR /app

COPY . .

ENV IBMCLOUD_API_KEY=<API_KEY>

# Comando para rodar a aplicação
RUN python -m pip install ibm_vpc
RUN python -m pip install ibm_cloud_sdk_core
# RUN python -m pip install os
CMD ["python", "rotina-vni-job.py"]
