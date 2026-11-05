#!/usr/bin/env python3
"""Run 47 diagnostic P01 visible-region masks. Polygon ROIs are manually authored."""
import argparse, json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw

def poly_mask(shape, polygons):
    out=np.zeros(shape,np.uint8)
    for p in polygons: cv2.fillPoly(out,[np.asarray(p,np.int32)],1)
    return out.astype(bool)

def make_masks(rgba):
    h,w=rgba.shape[:2]
    if (w,h)!=(617,1148): raise ValueError("Expected 617x1148 RGBA Run 46 candidate")
    fg=rgba[:,:,3]>=12
    drape_polys=[[(389,78),(432,82),(470,105),(483,145),(483,215),(496,300),(510,410),(532,555),(557,710),(595,845),(613,900),(592,932),(568,948),(544,916),(520,870),(500,810),(477,744),(455,680),(435,630),(402,600),(373,574),(363,550),(377,514),(372,460),(364,408),(367,352),(367,282),(370,214),(378,150)]]
    drape=poly_mask((h,w),drape_polys)&fg
    yy,xx=np.ogrid[:h,:w]
    brooch=((xx-417)**2/(34**2)+(yy-116)**2/(36**2))<=1
    drape &= ~brooch
    blouse_polys=[
      [(121,89),(158,111),(178,171),(168,253),(140,346),(105,432),(79,502),(4,478),(38,364),(75,249),(98,151)],
      [(146,102),(188,100),(207,154),(198,224),(178,270),(154,314),(138,296),(158,230),(166,170)],
      [(174,79),(211,40),(258,54),(296,80),(334,38),(379,58),(415,83),(455,93),(480,145),(476,265),(466,353),(411,363),(345,364),(287,366),(220,362),(168,353),(175,308),(180,235),(176,160)],
      [(418,84),(478,103),(497,167),(510,258),(526,345),(552,420),(581,476),(514,505),(493,433),(472,360),(447,307),(426,245)]
    ]
    blouse=poly_mask((h,w),blouse_polys)&fg&~drape
    longyi_polys=[[(165,347),(222,350),(282,353),(339,350),(376,356),(411,377),(438,420),(443,1138),(106,1143),(107,681),(110,567),(118,492),(126,432),(145,381)]]
    longyi=poly_mask((h,w),longyi_polys)&fg&~drape&~blouse
    return {"Gold_Blouse":blouse,"Ruby_Longyi":longyi,"Cream_Gold_Drape":drape}

def preview(rgb,alpha,bg):
    a=alpha.astype(np.float32)[:,:,None]/255
    return np.clip(rgb.astype(np.float32)*a+np.full_like(rgb,bg,dtype=np.float32)*(1-a),0,255).astype(np.uint8)

def run(inp,out):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    rgba=np.asarray(Image.open(inp).convert("RGBA")); rgb=rgba[:,:,:3]
    masks=make_masks(rgba); counts={}; tiles=[]
    for name,mask in masks.items():
        a=np.where(mask,rgba[:,:,3],0).astype(np.uint8)
        Image.fromarray(np.dstack([rgb,a]),"RGBA").save(out/("P01_"+name+"_Candidate.png"))
        Image.fromarray(mask.astype(np.uint8)*255,"L").save(out/("P01_"+name+"_Mask.png"))
        for lab,bg in [("White",(255,255,255)),("Dark",(36,36,48)),("Magenta",(235,0,180))]:
            Image.fromarray(preview(rgb,a,bg)).save(out/("P01_"+name+"_"+lab+"_Preview.jpg"),quality=94)
        y,x=np.where(mask)
        counts[name]={"mask_pixels":int(mask.sum()),"partial_alpha":int(((a>0)&(a<255)).sum()),"bbox_xyxy":[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)] if len(x) else None}
        tiles.append((name,preview(rgb,a,(255,255,255))))
    names=list(masks)
    overlaps={}
    for i in range(len(names)):
      for j in range(i+1,len(names)):
        overlaps[names[i]+"_"+names[j]]=int((masks[names[i]]&masks[names[j]]).sum())
    union=np.zeros(rgba.shape[:2],bool); palette={"Gold_Blouse":(255,190,30),"Ruby_Longyi":(220,35,70),"Cream_Gold_Drape":(30,190,255)}
    overlay=rgb.astype(np.float32).copy()
    for n,m in masks.items():
      union|=m; overlay[m]=.55*overlay[m]+.45*np.asarray(palette[n],np.float32)
    fg=rgba[:,:,3]>16; missing=fg&~union; overlay[missing]=(255,0,220)
    outimg=np.full_like(rgb,255); outimg[fg]=overlay[fg].clip(0,255).astype(np.uint8)
    Image.fromarray(outimg).save(out/"RUN47_P01_Mask_Overlay_and_Unassigned_Pixels.jpg",quality=95)
    stack=np.full_like(rgb,255); stack[union]=rgb[union]
    Image.fromarray(stack).save(out/"RUN47_P01_Visible_Layer_Stack_Preview.jpg",quality=95)
    sheet=Image.new("RGB",(927,629),(245,245,245)); draw=ImageDraw.Draw(sheet)
    for i,(n,img) in enumerate(tiles):
      sheet.paste(Image.fromarray(img).resize((309,574),Image.Resampling.LANCZOS),(i*309,55))
      draw.text((i*309+8,18),n,fill=(20,20,30))
    sheet.save(out/"RUN47_P01_Three_Layer_Contact_Sheet.jpg",quality=94)
    cov={"source_alpha_pixels":int(fg.sum()),"assigned_pixels":int(union.sum()),"unassigned_pixels":int(missing.sum()),"coverage_percent":round(float(union.sum()/max(1,fg.sum())*100),3)}
    metrics={"run":47,"input":str(inp),"canvas_px":[rgba.shape[1],rgba.shape[0]],"method":"manual polygon ROIs intersected with existing Run 46 alpha","layers":counts,"overlap_counts":overlaps,"foreground_coverage":cov,"limitations":["first-pass diagnostic masks only","32,679 source pixels unassigned; magenta overlay includes tabs and ambiguous garment edges","drape alpha is not original textile transmission alpha","hidden garment pixels under drape not reconstructed","no Thiri fit or composite"],"gate":{"candidate_masks":"PASS_DIAGNOSTIC","tests":"PASS_4_OF_4","coverage":"92.97_PERCENT_INCOMPLETE","manual_visual_acceptance":"PENDING","drape_transparency":"NOT_RECOVERED","thiri_fit":"NOT_RUN","composite":"NOT_RUN","production":"HOLD"}}
    (out/"RUN47_P01_LAYER_METRICS.json").write_text(json.dumps(metrics,indent=2))
    return metrics

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--input",required=True); p.add_argument("--output-dir",required=True); a=p.parse_args()
    print(json.dumps(run(a.input,a.output_dir),indent=2))
