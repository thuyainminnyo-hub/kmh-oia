#!/usr/bin/env python3
"""Diagnostic P01 extraction from the recovered master sheet; not a production matting tool."""
from pathlib import Path
import argparse, hashlib, json
import cv2
import numpy as np
from PIL import Image

CROP_XYXY=(1840,470,2640,1730)
TAB_BOXES=[(180,34,250,116),(443,26,523,122),(91,304,164,377),(625,300,701,378),(141,690,220,762)]

def fill_small_internal_holes(mask,max_area=90):
    result=(mask>0).astype(np.uint8); inv=1-result
    n,labels,stats,_=cv2.connectedComponentsWithStats(inv,8)
    h,w=result.shape
    for i in range(1,n):
        x,y,bw,bh,area=map(int,stats[i])
        if not (x==0 or y==0 or x+bw>=w or y+bh>=h) and area<=max_area:
            result[labels==i]=1
    return result

def make_candidate_mask(rgb):
    if rgb.ndim!=3 or rgb.shape[2]!=3: raise ValueError("Source crop must be RGB.")
    hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV); _,sat,val=cv2.split(hsv)
    raw=((sat>15)|(val<230)).astype(np.uint8)
    n,labels,stats,_=cv2.connectedComponentsWithStats(raw,8)
    if n<=1: raise ValueError("No foreground component found.")
    idx=1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]))
    base=(labels==idx).astype(np.uint8); candidate=base.copy()
    for x0,y0,x1,y1 in TAB_BOXES:
        candidate[y0:y1,x0:x1]=0
        colour=(sat[y0:y1,x0:x1]>25)&(val[y0:y1,x0:x1]>65)
        candidate[y0:y1,x0:x1][colour]=1
    n2,lab2,st2,_=cv2.connectedComponentsWithStats(candidate,8)
    idx2=1+int(np.argmax(st2[1:,cv2.CC_STAT_AREA]))
    candidate=(lab2==idx2).astype(np.uint8)
    candidate=fill_small_internal_holes(candidate,90)
    return candidate,{"component_count":int(n),"source_component_pixels":int(base.sum()),"candidate_pixels":int(candidate.sum()),"removed_pixels":int(base.sum()-candidate.sum())}

def build_rgba(rgb,mask):
    ys,xs=np.where(mask>0)
    if len(xs)==0: raise ValueError("Empty mask.")
    bbox=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
    x0,y0,x1,y1=bbox; colour=rgb[y0:y1,x0:x1].copy(); m=mask[y0:y1,x0:x1].astype(np.uint8)
    dist=cv2.distanceTransform(m,cv2.DIST_L2,5)
    alpha=np.where(m>0,255,0).astype(np.uint8); edge=(m>0)&(dist<=1.5)
    edge_alpha=np.clip((255-np.min(colour.astype(np.int16),axis=2))*1.45,75,255).astype(np.uint8)
    alpha[edge]=edge_alpha[edge]
    return np.dstack([colour,alpha]),bbox

def composite(rgba,bg):
    c=rgba[:,:,:3].astype(np.float32); a=rgba[:,:,3:4].astype(np.float32)/255
    b=np.asarray(bg,dtype=np.float32).reshape(1,1,3)
    return np.clip(c*a+b*(1-a),0,255).astype(np.uint8)

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def run(source_page,output):
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    page=np.asarray(Image.open(source_page).convert("RGB"))
    x0,y0,x1,y1=CROP_XYXY; crop=page[y0:y1,x0:x1].copy()
    Image.fromarray(crop).save(output/"P01_Outfit03_MasterCrop_SafeMargin.png")
    mask,mi=make_candidate_mask(crop); rgba,bbox=build_rgba(crop,mask); alpha=rgba[:,:,3]
    Image.fromarray(rgba,"RGBA").save(output/"P01_Outfit03_Transparent_Candidate_v2.png")
    Image.fromarray(mask*255,"L").save(output/"P01_Outfit03_Silhouette_Mask_v2.png")
    for name,bg in {"White":(255,255,255),"Dark":(35,35,45),"Magenta":(235,0,180)}.items():
        Image.fromarray(composite(rgba,bg)).save(output/f"P01_Run46_{name}_Preview_v2.jpg",quality=95)
    metrics={"run":46,"source_page":Path(source_page).name,"page_px":[int(page.shape[1]),int(page.shape[0])],"crop_xyxy":list(CROP_XYXY),"crop_px":[800,1260],"bbox_on_crop_xyxy":bbox,"output_px":[int(rgba.shape[1]),int(rgba.shape[0])],"mask":mi,"alpha":{"nonzero":int((alpha>0).sum()),"partial":int(((alpha>0)&(alpha<255)).sum()),"opaque":int((alpha==255).sum()),"transparent":int((alpha==0).sum())},"limits":["Flattened RGB source; true sheer shawl alpha not recovered.","Manual tab ROIs; residual edge artifacts require visual cleanup.","No missing geometry reconstructed.","No Thiri fit or composite."]}
    (output/"RUN46_P01_EXTRACTION_METRICS.json").write_text(json.dumps(metrics,indent=2))
    return metrics

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--source-page",required=True); p.add_argument("--output-dir",required=True); a=p.parse_args()
    print(json.dumps(run(a.source_page,a.output_dir),indent=2))
