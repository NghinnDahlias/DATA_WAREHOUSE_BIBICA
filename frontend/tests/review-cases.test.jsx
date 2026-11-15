// @vitest-environment jsdom
import {beforeEach,it,expect,vi} from 'vitest'
import {cleanup,render,screen,waitFor} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
const mocks=vi.hoisted(()=>({list:vi.fn(),detail:vi.fn(),themes:vi.fn(),filters:{from:'2026-01-01',to:'2026-10-18',category:'all'}}))
vi.mock('../src/context/FilterContext.jsx',()=>({useFilters:()=>({filters:mocks.filters})}))
vi.mock('../src/api/client.js',()=>({getReviewCases:mocks.list,getReviewCase:mocks.detail,getReviewThemes:mocks.themes}))
import ReviewCases from '../src/components/ReviewCases.jsx'
import Modal from '../src/components/Modal.jsx'
const row=(key)=>({case_key:key,star_level:1,product_name:`Bánh mẫu ${key}`,review_date:'2026-10-01',content_status:'READY',preview:'bánh bị vỡ'})
beforeEach(()=>{cleanup();vi.clearAllMocks();mocks.filters={from:'2026-01-01',to:'2026-10-18',category:'all'};mocks.themes.mockResolvedValue({labels:[]});mocks.list.mockResolvedValue({rows:[row(1),row(2)],total:7});mocks.detail.mockImplementation(async(_,key)=>({...row(key),labels:[],content:`Ý kiến đã che ${key}`}))})
it('reads a case, paginates and resets on topic changes using the same filters',async()=>{
 render(<ReviewCases/>);
 await screen.findByText('Ý kiến đã che 1')
 await userEvent.click(screen.getByRole('button',{name:/Bánh mẫu 2/}))
 await screen.findByText('Ý kiến đã che 2')
 await userEvent.click(screen.getByRole('button',{name:'Sau',exact:true}))
 await waitFor(()=>expect(mocks.list).toHaveBeenLastCalledWith(mocks.filters,expect.objectContaining({offset:4})))
 await userEvent.selectOptions(screen.getByLabelText('Chủ đề tiêu cực'),'product_breakage_mention')
 await waitFor(()=>expect(mocks.list).toHaveBeenLastCalledWith(mocks.filters,expect.objectContaining({offset:0,topic:'product_breakage_mention'})))
})
it('does not replace a newer selected case with a late previous response',async()=>{
 let release
 mocks.detail.mockImplementationOnce(()=>new Promise(resolve=>{release=resolve})).mockResolvedValueOnce({...row(2),labels:[],content:'Ý kiến case mới'})
 render(<ReviewCases/>);await screen.findByRole('button',{name:/Bánh mẫu 2/})
 await userEvent.click(screen.getByRole('button',{name:/Bánh mẫu 2/}));await screen.findByText('Ý kiến case mới')
 release({...row(1),labels:[],content:'Nội dung cũ'})
 await waitFor(()=>expect(screen.queryByText('Nội dung cũ')).toBeNull())
 expect(screen.getByText('Ý kiến case mới')).toBeTruthy()
})
it('states that a star-only review has no text and handles empty cohorts',async()=>{
 mocks.detail.mockResolvedValue({...row(1),labels:[],content_status:'NO_TEXT',content:''})
 const {rerender}=render(<ReviewCases/>);await screen.findByText('Khách chỉ chấm sao, không có nội dung.')
 mocks.list.mockResolvedValue({rows:[],total:0});mocks.filters={...mocks.filters,category:'Kẹo'};rerender(<ReviewCases/>)
 await screen.findByText(/Không có đánh giá khớp/)
 expect(screen.queryByRole('article')).toBeNull()
})
it('modal closes with Escape and restores focus',async()=>{
 const close=vi.fn();const button=document.createElement('button');document.body.append(button);button.focus()
 const {unmount}=render(<Modal title="Đọc ý kiến" onClose={close}><p>Nội dung mẫu</p></Modal>)
 expect(document.activeElement).toBe(screen.getByLabelText('Đóng cửa sổ'))
 await userEvent.keyboard('{Escape}');expect(close).toHaveBeenCalledOnce();unmount();expect(document.activeElement).toBe(button);button.remove()
})
