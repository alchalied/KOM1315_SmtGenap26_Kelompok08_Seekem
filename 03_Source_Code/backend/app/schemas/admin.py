from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Admin: Verification (Laporan) ──

class AdminReportResponse(BaseModel):
    """
    Format response untuk halaman AdminVerification & AdminReportDetail di FE.
    FE mengakses: report.id, report.name, report.status, report.image,
    report.location, report.time, report.category, report.tag,
    report.description, report.reporterName, report.reportTime, report.detailLocation
    """
    id: int
    name: str
    status: str          # "pending_verification", "verified", "rejected"
    image: Optional[str] = None
    location: str
    time: str
    category: str
    tag: str             # "Hilang" / "Temuan"
    description: Optional[str] = None
    reporterName: Optional[str] = None
    reportTime: Optional[str] = None
    detailLocation: Optional[str] = None


class AdminVerifyAction(BaseModel):
    """FE mengirim: { action: "approve" / "reject" }"""
    action: str


# ── Admin: Claims ──

class AdminClaimResponse(BaseModel):
    """
    Format response untuk halaman AdminClaims & AdminClaimDetail di FE.
    FE mengakses: claim.id, claim.itemName, claim.image, claim.ownerName,
    claim.nim, claim.faculty, claim.contact, claim.description,
    claim.evidenceImage, claim.location, claim.foundDate, claim.foundTime,
    claim.claimDate, claim.history, claim.adminNote, claim.status, claim.reportId
    """
    id: int
    itemName: str
    image: Optional[str] = None
    ownerName: Optional[str] = None
    nim: Optional[str] = None
    faculty: Optional[str] = None
    contact: Optional[str] = None
    description: Optional[str] = None
    evidenceImage: Optional[str] = None
    location: Optional[str] = None
    foundDate: Optional[str] = None
    foundTime: Optional[str] = None
    claimDate: Optional[str] = None
    history: Optional[str] = None
    adminNote: Optional[str] = None
    status: str
    reportId: Optional[int] = None


class AdminClaimCreate(BaseModel):
    """
    FE mengirim: { itemId, ownerName, nim, faculty, contact, description, evidenceImage }
    """
    itemId: int
    ownerName: str
    nim: Optional[str] = None
    faculty: Optional[str] = None
    contact: Optional[str] = None
    description: str
    evidenceImage: Optional[str] = None


class AdminClaimAction(BaseModel):
    """FE mengirim: { action: "approve" / "reject" }"""
    action: str

class AdminItemAction(BaseModel):
    """FE mengirim: { action: "delete" / "hold" / "post" / "cancel_claim" }"""
    action: str

