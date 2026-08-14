import type {Lead,LeadInput,PipelineResponse} from "./types";
const BASE=(import.meta.env.VITE_API_BASE_URL||"http://127.0.0.1:8000").replace(/\/$/,"");
async function req<T>(path:string,init:RequestInit={}):Promise<T>{
 const r=await fetch(BASE+path,{...init,headers:{"Content-Type":"application/json",...(init.headers||{})}});
 const data=await r.json().catch(()=>null);
 if(!r.ok) throw new Error(data?.detail||"Request failed. Please try again.");
 return data;
}
export const getLeads=()=>req<Lead[]>("/leads");
export const getLead=(id:number)=>req<Lead>(`/leads/${id}`);
export const createLead=(x:LeadInput)=>req<PipelineResponse>("/leads",{method:"POST",body:JSON.stringify(x)});
export const approveLead=(id:number)=>req(`/leads/${id}/approve`,{method:"POST",body:JSON.stringify({approved:true})});
export const rejectLead=(id:number)=>req(`/leads/${id}/approve`,{method:"POST",body:JSON.stringify({approved:false})});
export const sendLead=(id:number)=>req(`/leads/${id}/send`,{method:"POST"});
export const updateEmail=(id:number,subject:string,body:string)=>{const p=(import.meta.env.VITE_EMAIL_UPDATE_PATH||"/leads/{id}/email").replace("{id}",String(id));return req<Lead>(p,{method:"PATCH",body:JSON.stringify({subject,body})});};