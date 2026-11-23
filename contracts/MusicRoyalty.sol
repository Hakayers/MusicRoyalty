// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";

contract MusicRoyalty is ERC721 {

    // =====================================================
    // 1. DATA PIHAK DALAM SISTEM
    // =====================================================

    address payable public kreator;
    address payable public produser;
    address payable public penulisLagu;
    address payable public platformMusik;

    // =====================================================
    // 2. TOKEN ID DAN BATCH COUNTER
    // =====================================================

    uint256 private nextTokenId = 1;
    uint256 private batchCounter = 0;

    // =====================================================
    // 3. STRUCT DATA MUSIK
    // =====================================================

    struct MusicBatch {
        uint256 tokenId;
        string batchId;
        string judulMusik;
        string jenisTransaksi;
        address pemilikHakCipta;
        uint256 totalRoyalti;
        string status;
        bool exists;
    }

    struct RoyaltyDistribution {
        uint256 kreator;
        uint256 produser;
        uint256 penulisLagu;
        uint256 platformMusik;
    }

    struct History {
        string batchId;
        string aktivitas;
        uint256 waktu;
        address pelaku;
    }

    // =====================================================
    // 4. STORAGE
    // =====================================================

    mapping(string => MusicBatch) public batches;

    mapping(string => RoyaltyDistribution) public distributions;

    mapping(string => History[]) private histories;

    // =====================================================
    // 5. EVENTS
    // =====================================================

    event BatchCreated(
        string batchId,
        string judulMusik,
        address pemilik,
        uint256 tokenId
    );

    event MusicUsed(
        string batchId,
        string jenisPenggunaan
    );

    event RoyaltyDistributed(
        string batchId,
        uint256 totalRoyalti
    );

    event RoyaltyPaid(
        string batchId,
        uint256 totalRoyalti
    );

    // =====================================================
    // 6. CONSTRUCTOR
    // =====================================================

    constructor(
        address payable _kreator,
        address payable _produser,
        address payable _penulisLagu,
        address payable _platformMusik
    ) ERC721("Music Royalty", "MUSIC") {

        require(_kreator != address(0), "Alamat kreator tidak valid");
        require(_produser != address(0), "Alamat produser tidak valid");
        require(_penulisLagu != address(0), "Alamat penulis tidak valid");
        require(_platformMusik != address(0), "Alamat platform tidak valid");

        kreator = _kreator;
        produser = _produser;
        penulisLagu = _penulisLagu;
        platformMusik = _platformMusik;
    }

    // =====================================================
    // 7. FUNGSI MINT NFT SESUAI MODUL
    // =====================================================

    function mint(address to)
        public
        returns (uint256)
    {
        require(msg.sender == kreator, "Hanya kreator yang boleh mint");
        require(to != address(0), "Alamat penerima tidak valid");

        uint256 tokenId = nextTokenId;
        nextTokenId++;

        _safeMint(to, tokenId);

        return tokenId;
    }

    // =====================================================
    // 8. CEK PEMILIK NFT
    // =====================================================

    function getOwner(uint256 tokenId)
        public
        view
        returns (address)
    {
        return ownerOf(tokenId);
    }

    // =====================================================
    // 9. MEMBUAT BATCH MUSIK + NFT
    // =====================================================

    function createBatch(
        string memory _judulMusik,
        string memory _jenisTransaksi
    ) public returns (uint256) {

        require(msg.sender == kreator, "Hanya kreator yang boleh membuat batch");
        require(bytes(_judulMusik).length > 0, "Judul musik wajib diisi");
        require(bytes(_jenisTransaksi).length > 0, "Jenis transaksi wajib diisi");

        batchCounter++;

        string memory idBatch = string(
            abi.encodePacked("MUSIC-", uint2str(batchCounter))
        );

        uint256 tokenId = nextTokenId;
        nextTokenId++;

        // NFT langsung dibuat untuk kreator.
        _safeMint(kreator, tokenId);

        // Data musik terhubung dengan tokenId.
        batches[idBatch] = MusicBatch({
            tokenId: tokenId,
            batchId: idBatch,
            judulMusik: _judulMusik,
            jenisTransaksi: _jenisTransaksi,
            pemilikHakCipta: kreator,
            totalRoyalti: 0,
            status: "CREATED",
            exists: true
        });

        histories[idBatch].push(
            History({
                batchId: idBatch,
                aktivitas: "Batch musik dibuat dan NFT di-mint",
                waktu: block.timestamp,
                pelaku: msg.sender
            })
        );

        emit BatchCreated(
            idBatch,
            _judulMusik,
            kreator,
            tokenId
        );

        return tokenId;
    }

    // =====================================================
    // 10. MENCATAT PENGGUNAAN MUSIK
    // =====================================================

    function recordMusicUsage(
        string memory _batchId,
        string memory _jenisPenggunaan
    ) public {

        require(batches[_batchId].exists, "Batch tidak ditemukan");
        require(msg.sender == platformMusik, "Hanya platform musik");
        require(bytes(_jenisPenggunaan).length > 0, "Jenis penggunaan wajib diisi");
        require(
            keccak256(bytes(batches[_batchId].status)) ==
            keccak256(bytes("CREATED")),
            "Status batch tidak sesuai"
        );

        batches[_batchId].status = "USED";

        histories[_batchId].push(
            History({
                batchId: _batchId,
                aktivitas: _jenisPenggunaan,
                waktu: block.timestamp,
                pelaku: msg.sender
            })
        );

        emit MusicUsed(_batchId, _jenisPenggunaan);
    }

    // =====================================================
    // 11. MENGHITUNG DAN MENDISTRIBUSIKAN ROYALTI
    // =====================================================

    function distributeRoyalty(
        string memory _batchId,
        uint256 _totalRoyalti
    ) public {

        require(batches[_batchId].exists, "Batch tidak ditemukan");
        require(msg.sender == platformMusik, "Hanya platform musik");
        require(_totalRoyalti > 0, "Total royalti harus lebih dari 0");
        require(
            keccak256(bytes(batches[_batchId].status)) ==
            keccak256(bytes("USED")),
            "Musik belum digunakan"
        );

        batches[_batchId].totalRoyalti = _totalRoyalti;
        batches[_batchId].status = "DISTRIBUTED";

        distributions[_batchId] = RoyaltyDistribution({
            kreator: (_totalRoyalti * 60) / 100,
            produser: (_totalRoyalti * 20) / 100,
            penulisLagu: (_totalRoyalti * 15) / 100,
            platformMusik: (_totalRoyalti * 5) / 100
        });

        histories[_batchId].push(
            History({
                batchId: _batchId,
                aktivitas: "Royalti dihitung dan didistribusikan",
                waktu: block.timestamp,
                pelaku: msg.sender
            })
        );

        emit RoyaltyDistributed(_batchId, _totalRoyalti);
    }

    // =====================================================
    // 12. MEMBAYAR ROYALTI
    // =====================================================

    function payRoyalty(
        string memory _batchId
    ) public payable {

        require(batches[_batchId].exists, "Batch tidak ditemukan");
        require(msg.sender == platformMusik, "Hanya platform musik");
        require(
            keccak256(bytes(batches[_batchId].status)) ==
            keccak256(bytes("DISTRIBUTED")),
            "Royalti belum didistribusikan"
        );
        require(
            msg.value == batches[_batchId].totalRoyalti,
            "Jumlah ETH tidak sesuai"
        );

        RoyaltyDistribution memory royalty = distributions[_batchId];

        // Ubah status sebelum mengirim pembayaran.
        batches[_batchId].status = "COMPLETED";

        (bool successKreator, ) =
            kreator.call{value: royalty.kreator}("");
        require(successKreator, "Pembayaran kreator gagal");

        (bool successProduser, ) =
            produser.call{value: royalty.produser}("");
        require(successProduser, "Pembayaran produser gagal");

        (bool successPenulis, ) =
            penulisLagu.call{value: royalty.penulisLagu}("");
        require(successPenulis, "Pembayaran penulis gagal");

        (bool successPlatform, ) =
            platformMusik.call{value: royalty.platformMusik}("");
        require(successPlatform, "Pembayaran platform gagal");

        histories[_batchId].push(
            History({
                batchId: _batchId,
                aktivitas: "Royalti dibayarkan kepada seluruh pihak",
                waktu: block.timestamp,
                pelaku: msg.sender
            })
        );

        emit RoyaltyPaid(
            _batchId,
            batches[_batchId].totalRoyalti
        );
    }

    // =====================================================
    // 13. MELIHAT DATA MUSIK
    // =====================================================

    function getMusic(string memory _batchId)
        public
        view
        returns (
            uint256 tokenId,
            string memory batchId,
            string memory judulMusik,
            string memory jenisTransaksi,
            address pemilikHakCipta,
            uint256 totalRoyalti,
            string memory status
        )
    {
        require(batches[_batchId].exists, "Batch tidak ditemukan");

        MusicBatch memory batch = batches[_batchId];

        return (
            batch.tokenId,
            batch.batchId,
            batch.judulMusik,
            batch.jenisTransaksi,
            batch.pemilikHakCipta,
            batch.totalRoyalti,
            batch.status
        );
    }

    // =====================================================
    // 14. MELIHAT DISTRIBUSI ROYALTI
    // =====================================================

    function getRoyaltyDistribution(string memory _batchId)
        public
        view
        returns (
            uint256,
            uint256,
            uint256,
            uint256
        )
    {
        require(batches[_batchId].exists, "Batch tidak ditemukan");

        RoyaltyDistribution memory royalty = distributions[_batchId];

        return (
            royalty.kreator,
            royalty.produser,
            royalty.penulisLagu,
            royalty.platformMusik
        );
    }

    // =====================================================
    // 15. MELIHAT JUMLAH RIWAYAT
    // =====================================================

    function getHistoryCount(string memory _batchId)
        public
        view
        returns (uint256)
    {
        require(batches[_batchId].exists, "Batch tidak ditemukan");
        return histories[_batchId].length;
    }

    // =====================================================
    // 16. MELIHAT RIWAYAT TRANSAKSI
    // =====================================================

    function getHistory(
        string memory _batchId,
        uint256 _index
    ) public view returns (
        string memory,
        string memory,
        uint256,
        address
    ) {
        require(batches[_batchId].exists, "Batch tidak ditemukan");
        require(
            _index < histories[_batchId].length,
            "Index riwayat tidak valid"
        );

        History memory history = histories[_batchId][_index];

        return (
            history.batchId,
            history.aktivitas,
            history.waktu,
            history.pelaku
        );
    }

    // =====================================================
    // 17. MELIHAT ALAMAT SEMUA PIHAK
    // =====================================================

    function getParticipants()
        public
        view
        returns (address, address, address, address)
    {
        return (
            kreator,
            produser,
            penulisLagu,
            platformMusik
        );
    }

    // =====================================================
    // 18. KONVERSI UINT KE STRING
    // =====================================================

    function uint2str(uint256 _i)
        internal
        pure
        returns (string memory)
    {
        if (_i == 0) {
            return "0";
        }

        uint256 j = _i;
        uint256 length;

        while (j != 0) {
            length++;
            j /= 10;
        }

        bytes memory bstr = new bytes(length);
        uint256 k = length;

        while (_i != 0) {
            k--;

            bstr[k] = bytes1(
                uint8(48 + (_i % 10))
            );

            _i /= 10;
        }

        return string(bstr);
    }
}