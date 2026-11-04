"""Decode the supplied Ratings scraper sheet; never emit buyer/free-text fields."""
import re
from .common import clean,norm,date,digest

def project_scraped_rating(row,product_names=None):
    fields=['data'+str(i) for i in range(2,12)]
    # The source retains full lexical IDs inside its DOM text. Never stringify
    # a numeric Excel cell as an ID; recover only from these independent strings.
    lexical=lambda value,length:re.findall(r'(?<!\d)\d{'+str(length)+r'}(?!\d)',value) if isinstance(value,str) else []
    orders=set(lexical(row.get('data'),18))
    markers=[(key,value) for key in ('data2','data3','data4','data5') for value in lexical(row.get(key),19)]
    products={value for _,value in markers}
    oid=next(iter(orders)) if len(orders)==1 else ''
    pid=next(iter(products)) if len(products)==1 else ''
    product_field='data'+str(int(markers[0][0][4:])+1) if len(markers)==1 and pid else None
    product=clean(row.get(product_field)) if product_field else ''
    offset=int(product_field[4:]) if product_field else None
    variant=clean(row.get('data'+str(offset+1))) if offset else ''
    text=clean(row.get('data'+str(offset+2))) if offset else ''
    # Scraper DOM order: first date is the review; subsequent dates include replies.
    review_date=next((date(row.get(key)) for key in fields if date(row.get(key))),None)
    if date(text):text=''
    signature=digest('\x1f'.join(norm(v) for v in [oid,pid,row.get('name'),product,variant,row.get('rating'),review_date,text]))
    ids_valid=bool(oid and pid)
    id_status=('EXACT_TEXT_IDS' if isinstance(row.get('order_id'),str) and isinstance(row.get('product_id'),str) and row['order_id']==oid and row['product_id']==pid
               else 'RECOVERED_FROM_EMBEDDED_TEXT') if ids_valid else 'UNVERIFIABLE_IDS'
    return {'order_id':oid,'product_id':pid,'product_name':product,
            'star_level':row.get('rating'),'review_date':review_date,'review_text':text,
            'review_signature':signature,'review_id_status':id_status,'review_layout_status':'PRODUCT_ID_ANCHOR' if product_field else 'UNRESOLVED_LAYOUT'}
