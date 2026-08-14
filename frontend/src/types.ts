export type Lead={
 id:number; name:string; email:string; company:string; website?:string|null;
 job_title?:string|null; message:string; created_at?:string|null;
 industry?:string|null; company_size?:number|null; lead_volume?:number|null;
 problem?:string|null; urgency?:string|null; score?:number|null; category?:string|null;
 score_reasons?:string[]; research_summary?:string|null; research_data?:CompanyResearch|null;
 research_sources?:string[]; email_subject?:string|null; email_body?:string|null;
 email_status?:string|null; sent_at?:string|null;
};
export type CompanyResearch={
 company_name:string; industry?:string|null; description:string;
 products_or_services:string[]; target_customers?:string|null; company_size?:number|null;
 summary:string; source_urls:string[];
};
export type LeadInput={name:string;email:string;company:string;website?:string;job_title?:string;message:string};
export type PipelineResponse={lead:Lead;analysis:any;score:any;research:CompanyResearch;email:{subject:string;body:string}};