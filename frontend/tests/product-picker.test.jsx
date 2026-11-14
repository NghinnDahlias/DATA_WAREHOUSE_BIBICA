// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest'
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react'
const searchProducts=vi.fn()
vi.mock('../src/api/client.js',()=>({searchProducts}))
const {default:ProductPicker}=await import('../src/components/ProductPicker.jsx')
afterEach(()=>{cleanup();searchProducts.mockReset()})
const filters={store:'all'}
const item=(key)=>({key,label:'Same cake',store:'bibica_official_store',sku:`200000000000000000${key}`,variation:`Variant ${key}`,orders:100-key,total:25})
it('shows distinct same-name SKU identities, pages results and retains selection',async()=>{
 searchProducts.mockImplementation(async(f,q,n,offset)=>Array.from({length:Math.min(10,25-offset)},(_,i)=>item(offset+i+1)))
 const onChange=vi.fn()
 const {rerender}=render(<ProductPicker label="Sản phẩm" value={null} onChange={onChange} baseFilters={filters}/> )
 fireEvent.focus(screen.getByLabelText('Sản phẩm'))
 await waitFor(()=>expect(screen.getByText(/SKU 2000000000000000001$/)).toBeTruthy())
 expect(screen.getAllByText('Same cake')).toHaveLength(10)
 fireEvent.click(screen.getByText('Sau'))
 await waitFor(()=>expect(searchProducts).toHaveBeenLastCalledWith(expect.anything(),'',10,10))
 await waitFor(()=>expect(screen.getByText(/SKU 20000000000000000011$/)).toBeTruthy())
 fireEvent.click(screen.getByText(/SKU 20000000000000000011$/).closest('button'))
 expect(onChange).toHaveBeenCalledWith(item(11))
 rerender(<ProductPicker label="Sản phẩm" value={item(11)} onChange={onChange} baseFilters={filters}/> )
 expect(screen.getByRole('button',{name:'Đổi sản phẩm'}).textContent).toContain('Variant 11')
 fireEvent.click(screen.getByRole('button',{name:'Đổi sản phẩm'}))
 expect(screen.getByLabelText('Tìm SKU thay thế')).toBeTruthy()
})
it('ignores an old search response after a newer query completes',async()=>{
 let finishOld
 searchProducts.mockImplementation((f,q)=>q==='new'?Promise.resolve([{...item(2),label:'New result'}]):new Promise(resolve=>{finishOld=resolve}))
 render(<ProductPicker label="Sản phẩm" onChange={()=>{}} baseFilters={filters}/> )
 fireEvent.focus(screen.getByLabelText('Sản phẩm'))
 await waitFor(()=>expect(finishOld).toBeTypeOf('function'))
 fireEvent.change(screen.getByLabelText('Sản phẩm'),{target:{value:'new'}})
 await screen.findByText('New result')
 finishOld([{...item(1),label:'Old result'}])
 await new Promise(resolve=>setTimeout(resolve,20))
 expect(screen.queryByText('Old result')).toBeNull()
 expect(screen.getByText('New result')).toBeTruthy()
})
