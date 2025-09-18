import http from "./http";

export const getDocumentDetail = (documentid) => {
  console.log("Calling document detail API with ID:", documentid);
  return http.get("knowledge/documents/detail/", {
    params: { documentid },
  });
};
