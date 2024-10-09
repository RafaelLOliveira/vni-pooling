# /////////////////////////////////////////////////////////////
# 
# 
# Rotina para fazer Pooling da VNI entre VSIs Ativo e Passivo
# 
# 
# OBS1: input é apenas os IDs das VSIs
# OBS2: precisa criar VNI antes e atachar na VSI
# 
# /////////////////////////////////////////////////////////////

from ibm_vpc import VpcV1 
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator 
import os, time
from os import environ

apikey = environ.get('IBMCLOUD_API_KEY')

authenticator = IAMAuthenticator(apikey)
service = VpcV1(authenticator=authenticator)
service.set_service_url('https://br-sao.iaas.cloud.ibm.com/v1')

# IDs das VSIs
vsi1_id="02u7_59bddc6a-02fe-4c21-80ba-70a61d43d2e9"
vsi2_id="02u7_cbe266c5-456c-4b12-ba3d-7afbdb97c567"

reserved_ip_eth0_vsi1 = subnet_id_eth1_vsi1 = vni_id_eth1_vsi1 = attachment_id_eth1_vsi1 = None

def defineAtivoPassivo(fip_1, fip_2, vsi1_id, vsi2_id): # Define qual é Ativo e Passivo
    try:
        importDadosVNI(vsi1_id)
    except:
        fip_ativo = fip_2
        vsi_ativo_id = vsi2_id
        fip_passivo = fip_1
        vsi_passivo_id = vsi1_id

    try:
        importDadosVNI(vsi2_id)
    except:
        fip_ativo = fip_1
        vsi_ativo_id = vsi1_id
        fip_passivo = fip_2
        vsi_passivo_id = vsi2_id

    return fip_ativo, vsi_ativo_id, fip_passivo, vsi_passivo_id

def ping(fip): # função ping no IP
    resposta = 0
    quantidade_ping = 3
    ciclos = 1
    resultado_ciclo = numero_de_ping = sucesso_ping = falha_ping = 0
    for num1 in range(ciclos):
        for num2 in range(quantidade_ping):
            response_fip = os.system(f"ping -c 1 {fip}")
            print(response_fip) # response_fip zero é sucesso
            time.sleep(1)   # espera 1 segundo entre pings
            numero_de_ping += 1
            if response_fip == 0:
                sucesso_ping += 1
            else:
                falha_ping += 1    
        if sucesso_ping > falha_ping:
            print("/////// Sucesso no ciclo de ping /////// ")
            resultado_ciclo += 1
        else:
            print(" ///////Falha no ciclo de ping ///////")
        sucesso_ping = 0
        falha_ping = 0 
            
    if resultado_ciclo != ciclos: # se todos os ciclos falharem, o ativo está desligado
        print("/////// Ativo desligado ///////") 
    else:
        print(" /////// Ativo funcionando ///////") 
        resposta += 1
    return resposta
        
def reservedIpVsi(vsi_id): # pega Reserved IP da primeira interface VSI 
    response = service.list_instance_network_attachments(
        instance_id=vsi_id,
    )
    instance_network_attachment_collection = response.get_result()
    reserved_ip_eth0_vsi = instance_network_attachment_collection["network_attachments"][0]["primary_ip"]["address"]
    return reserved_ip_eth0_vsi

def importDadosVNI(vsi_id): # pega ID da VNI
    response = service.list_instance_network_attachments(
        instance_id=vsi_id,
    )
    instance_network_attachment_collection = response.get_result()
    vni_id_eth1_ativa = instance_network_attachment_collection["network_attachments"][1]["virtual_network_interface"]["id"]
    attachment_id_eth1_ativa = instance_network_attachment_collection["network_attachments"][1]["id"] 

    return vni_id_eth1_ativa, attachment_id_eth1_ativa 

def detachVniAtivo(attachment_id_eth1_ativa,vsi_ativo_id): # detach da VNI da VSI Ativa
    response = service.delete_instance_network_attachment(
        instance_id=vsi_ativo_id,
        id=attachment_id_eth1_ativa,
    )
    instance_network_attachment = response.get_result()
    print("/////// Detach realizado da VNI do Ativo! ///////")


def attachVniPassivo(vni_id_eth1_ativo, vsi_passivo_id): # attach VNI na VSI Passiva
    subnet_identity_model = {}
    subnet_identity_model['id'] = subnet_id_eth1_vsi1
    instance_network_attachment_prototype_virtual_network_interface_model = {
        'id':vni_id_eth1_ativo,
    }
    time.sleep(5)
    response = service.create_instance_network_attachment(
        instance_id=vsi_passivo_id,
        name='eth1',
        virtual_network_interface=instance_network_attachment_prototype_virtual_network_interface_model,
    )
    instance_network_attachment = response.get_result()

    print("/////// Attach realizado da VNI do Passivo! ///////")

def main(vsi1_id, vsi2_id):
    reserved_ip_eth0_vsi1 = reservedIpVsi(vsi1_id)
    reserved_ip_eth0_vsi2 = reservedIpVsi(vsi2_id)   

    reserved_ip_ativo, vsi_ativo_id, reserved_ip_passivo, vsi_passivo_id = defineAtivoPassivo(reserved_ip_eth0_vsi1, reserved_ip_eth0_vsi2, vsi1_id, vsi2_id)

    resposta = ping(reserved_ip_ativo)

    if resposta == 0:
        vni_id_eth1_ativa, attachment_id_eth1_ativa = importDadosVNI(vsi_ativo_id)
        detachVniAtivo(attachment_id_eth1_ativa,vsi_ativo_id)
        attachVniPassivo(vni_id_eth1_ativa, vsi_passivo_id)



main(vsi1_id, vsi2_id) # executa a main
