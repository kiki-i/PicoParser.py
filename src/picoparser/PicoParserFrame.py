from dataclasses import dataclass

import numpy as np

from .libpico import LibpicoFrame

INTERP_SUB = np.array([-1, 0, 1])


@dataclass
class Ieee80211MacFrameHeaderControlField:
  version: int
  type: int
  subtype: int
  toDS: int
  fromDS: int
  moreFrags: int
  retry: int
  powerMgmt: int
  more: int
  protect: int
  order: int


@dataclass
class StandardHeader:
  controlField: Ieee80211MacFrameHeaderControlField
  addr1: np.ndarray
  addr2: np.ndarray
  addr3: np.ndarray
  frag: int
  seq: int


@dataclass
class RxSBasic:
  deviceType: int
  tstamp: int
  systemTime: int
  centerFreq: int
  controlFreq: int
  cbw: int
  packetFormat: int
  pktCbw: int
  guardInterval: int
  mcs: int
  numSTS: int
  numESS: int
  numRx: int
  noiseFloor: int
  rssi: int


@dataclass
class RxExtraInfo:
  featureCode: int
  length: int
  version: int
  macAddrRom: np.ndarray
  macAddrCur: np.ndarray
  channelSelect: int
  bmode: int
  evm: np.ndarray
  txChainMask: int
  rxChainMask: int
  txPower: int
  cf: int
  txTsf: int
  lastHwTxTsf: int
  channelFlags: int
  txNess: int
  tuningPolicy: int
  pllRate: int
  pllRefdiv: int
  pllClockSelect: int
  agc: int
  antSelect: np.ndarray
  samplingRate: int
  cfo: int
  sfo: int


@dataclass
class Csi:
  deviceType: int
  firmwareVersion: int
  packetFormat: int
  cbw: int
  carrierFreq: int
  samplingRate: int
  subcarrierBandwidth: int
  antSelect: int
  subcarrierOffset: int
  nTones: int
  nTx: int
  nRx: int
  nEss: int
  nCsi: int
  subcarrierIndices: np.ndarray
  csi: np.ndarray
  magnitude: np.ndarray
  phase: np.ndarray


@dataclass
class PicoParserFrame:
  standardHeader: StandardHeader
  rxSBasic: RxSBasic
  rxExtraInfo: RxExtraInfo
  csi: Csi


def removeSubcarrierInterp(csi: np.ndarray, subcarrierIdx: np.ndarray) -> np.ndarray:
  realSubcarrierIdx = np.nonzero(~np.isin(subcarrierIdx, INTERP_SUB))[0]
  return csi[realSubcarrierIdx]


def libpicoFrameToPicoParserFrame(src: LibpicoFrame, interp: bool) -> PicoParserFrame:
  controlField = Ieee80211MacFrameHeaderControlField(
    version=src.standardHeader.controlField.version,
    type=src.standardHeader.controlField.type,
    subtype=src.standardHeader.controlField.subtype,
    toDS=src.standardHeader.controlField.toDS,
    fromDS=src.standardHeader.controlField.fromDS,
    moreFrags=src.standardHeader.controlField.moreFrags,
    retry=src.standardHeader.controlField.retry,
    powerMgmt=src.standardHeader.controlField.powerMgmt,
    more=src.standardHeader.controlField.more,
    protect=src.standardHeader.controlField.protect,
    order=src.standardHeader.controlField.order,
  )

  standardHeader = StandardHeader(
    controlField=controlField,
    addr1=np.ctypeslib.as_array(src.standardHeader.addr1).copy(),
    addr2=np.ctypeslib.as_array(src.standardHeader.addr2).copy(),
    addr3=np.ctypeslib.as_array(src.standardHeader.addr3).copy(),
    frag=src.standardHeader.frag,
    seq=src.standardHeader.seq,
  )

  rxSBasic = RxSBasic(
    deviceType=src.rxSBasic.deviceType,
    tstamp=src.rxSBasic.tstamp,
    systemTime=src.rxSBasic.systemTime,
    centerFreq=src.rxSBasic.centerFreq,
    controlFreq=src.rxSBasic.controlFreq,
    cbw=src.rxSBasic.cbw,
    packetFormat=src.rxSBasic.packetFormat,
    pktCbw=src.rxSBasic.pktCbw,
    guardInterval=src.rxSBasic.guardInterval,
    mcs=src.rxSBasic.mcs,
    numSTS=src.rxSBasic.numSTS,
    numESS=src.rxSBasic.numESS,
    numRx=src.rxSBasic.numRx,
    noiseFloor=src.rxSBasic.noiseFloor,
    rssi=src.rxSBasic.rssi,
  )

  rxExtraInfo = RxExtraInfo(
    featureCode=src.rxExtraInfo.featureCode,
    length=src.rxExtraInfo.length,
    version=src.rxExtraInfo.version,
    macAddrRom=np.ctypeslib.as_array(src.rxExtraInfo.macAddrRom).copy(),
    macAddrCur=np.ctypeslib.as_array(src.rxExtraInfo.macAddrCur).copy(),
    channelSelect=src.rxExtraInfo.channelSelect,
    bmode=src.rxExtraInfo.bmode,
    evm=np.ctypeslib.as_array(src.rxExtraInfo.evm).copy(),
    txChainMask=src.rxExtraInfo.txChainMask,
    rxChainMask=src.rxExtraInfo.rxChainMask,
    txPower=src.rxExtraInfo.txPower,
    cf=src.rxExtraInfo.cf,
    txTsf=src.rxExtraInfo.txTsf,
    lastHwTxTsf=src.rxExtraInfo.lastHwTxTsf,
    channelFlags=src.rxExtraInfo.channelFlags,
    txNess=src.rxExtraInfo.txNess,
    tuningPolicy=src.rxExtraInfo.tuningPolicy,
    pllRate=src.rxExtraInfo.pllRate,
    pllRefdiv=src.rxExtraInfo.pllRefdiv,
    pllClockSelect=src.rxExtraInfo.pllClockSelect,
    agc=src.rxExtraInfo.agc,
    antSelect=np.ctypeslib.as_array(src.rxExtraInfo.antSelect).copy(),
    samplingRate=src.rxExtraInfo.samplingRate,
    cfo=src.rxExtraInfo.cfo,
    sfo=src.rxExtraInfo.sfo,
  )

  shape: tuple = (
    src.csi.nTones,
    src.csi.nTx,
    src.csi.nRx,
    src.csi.nEss + src.csi.nCsi,
  )

  realNdarray = np.ctypeslib.as_array(src.csi.csiRealPtr, shape)
  imgNdarray = np.ctypeslib.as_array(src.csi.csiImagPtr, shape)
  csiNdarray = realNdarray + 1j * imgNdarray

  magNdarray = np.ctypeslib.as_array(src.csi.magnitudePtr, shape)
  phaseNdarray = np.ctypeslib.as_array(src.csi.phasePtr, shape)

  if not interp:
    subcarrierIndices = np.ctypeslib.as_array(
      src.csi.subcarrierIndicesPtr, (src.csi.subcarrierIndicesSize,)
    )
    csiNdarray = removeSubcarrierInterp(csiNdarray, subcarrierIndices)
    magNdarray = removeSubcarrierInterp(magNdarray, subcarrierIndices)
    phaseNdarray = removeSubcarrierInterp(phaseNdarray, subcarrierIndices)
  else:
    csiNdarray = csiNdarray.copy()
    magNdarray = magNdarray.copy()
    phaseNdarray = phaseNdarray.copy()

  csi = Csi(
    deviceType=src.csi.deviceType,
    firmwareVersion=src.csi.firmwareVersion,
    packetFormat=src.csi.packetFormat,
    cbw=src.csi.cbw,
    carrierFreq=src.csi.carrierFreq,
    samplingRate=src.csi.samplingRate,
    subcarrierBandwidth=src.csi.subcarrierBandwidth,
    antSelect=src.csi.antSelect,
    subcarrierOffset=src.csi.subcarrierOffset,
    nTones=src.csi.nTones,
    nTx=src.csi.nTx,
    nRx=src.csi.nRx,
    nEss=src.csi.nEss,
    nCsi=src.csi.nCsi,
    subcarrierIndices=subcarrierIndices,
    csi=csiNdarray,
    magnitude=magNdarray,
    phase=phaseNdarray,
  )

  return PicoParserFrame(standardHeader, rxSBasic, rxExtraInfo, csi)
