#!/usr/bin/env python3
"""Candidate semantic layer masks for MLCW P01; not final traced masks."""
import argparse, hashlib, json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw


def segment_masks(source_rgba):
    source_rgba=np.asarray(source_rgba)
    if source_rgba.ndim != 3 or source_rgba.shape[2] != 4:
        raise ValueError("Input must be an RGBA image")
    rgb=source_rgba[:,:,:3]
    alpha=source_rgba[:,:,3]
    hgt,wid=alpha.shape
    h,s,v=cv2.split(cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV))
    y,x=np.mgrid[:hgt,:wid]
    valid=alpha>=128
    blouse_roi=(y>=28)&(y<=165)&(x<=166)
    blouse_color=(h>=10)&(h<=38)&(s>=65)&(v>=80)
    blouse=valid&blouse_roi&blouse_color
    n,lab,stats,_=cv2.connectedComponentsWithStats(blouse.astype(np.uint8),8)
    keep=np.zeros_like(blouse)
    for i in range(1,n):
        if stats[i,cv2.CC_STAT_AREA]>=8: keep |= lab==i
    blouse=keep
    long_roi=(y>=142)&(y<=430)&(x<=137)
    red=((h<=12)|(h>=170))&(s>=65)&(v>=35)
    longyi=valid&long_roi&red
    skirt_poly=np.zeros((hgt,wid),np.uint8)
    cv2.fillPoly(skirt_poly,[np.array([[5,145],[126,150],[130,426],[5,430]],np.int32)],1)
    gold=(valid&(skirt_poly>0)&(h>=10)&(h<=38)&(s>=65)&(v>=75)&(y>=145))
    red_support=cv2.dilate(longyi.astype(np.uint8),np.ones((13,13),np.uint8))>0
    longyi |= gold&red_support
    drape_poly=np.zeros((hgt,wid),np.uint8)
    cv2.fillPoly(drape_poly,[np.array([[93,58],[130,59],[158,90],[169,157],[184,287],[177,365],[144,337],[127,270],[111,212],[96,158]],np.int32)],1)
    cream=(h>=8)&(h<=42)&(s>=25)&(v>=110)
    drape=valid&(drape_poly>0)&cream
    return {"gold_blouse":blouse,"ruby_longyi":longyi,"cream_gold_drape":drape}


def process(input_path, output_dir):
    output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=True)
    image=Image.open(input_path).convert('RGBA')
    rgba=np.asarray(image); rgb=rgba[:,:,:3]; alpha=rgba[:,:,3]
    hgt,wid=alpha.shape
    masks=segment_masks(rgba)
    names={"gold_blouse":"Gold_Blouse","ruby_longyi":"Ruby_Longyi","cream_gold_drape":"Cream_Gold_Drape"}
    for key,mask in masks.items():
        name=names[key]; layer=rgba.copy(); layer[:,:,3]=np.where(mask,alpha,0).astype(np.uint8)
        Image.fromarray(layer,'RGBA').save(output_dir/f'P01_{name}_Candidate.png')
        Image.fromarray((mask*255).astype('uint8'),'L').save(output_dir/f'P01_{name}_Mask.png')
    return masks


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',required=True); ap.add_argument('--output-dir',required=True)
    args=ap.parse_args()
    masks=process(args.input,args.output_dir)
    print({k:int(v.sum()) for k,v in masks.items()})
